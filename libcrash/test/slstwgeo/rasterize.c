#include "rasterize.h"

#define minmax_3(mn,mx,a,b,c) \
mn=a;mx=b; \
if(b<mn){mn=b;mx=a;} \
if(c<mn)mn=c; \
else if(c>mx)mx=c;

#define gfx_bounds_test(x,y,w,h) (((x) > (0)) && ((y) > (0)) \
                               && ((x) < (w)) && ((y) < (h)))
#define gfx_pixel_idx(x,y,w,h) ((((y)*(w))+(x))*3)

void draw_polys_zbuf(poly_id *poly_ids, fpoly *polys, 
                     int poly_count, 
                     int w, int h, z_struct *z_buf) {
  int i, ii, idx, x, y;
  fpoly *poly;
  float x0,y0,z0,x1,y1,z1,x2,y2,z2,w0,w1,w2;
  double x10,x21,x02,y10,y21,y02;
  double ad,bd,gd;
  double a,b,g;
  float f_min, f_max;
  int xmin,ymin,xmax,ymax;
  int xmin_idx, xmax_idx, xm_idx, ym_idx, ymin_idx, ymax_idx;
  int diffx;
  double det[3];
  float z;
  int check;
  
  for (i=0;i<poly_count;i++) {
    poly = &polys[i];
    
    
    #define load_vert(vx,vy,vz,v) vx=v.x;vy=v.y;vz=v.z;
    load_vert(x0,y0,z0,poly->verts[0]);
    load_vert(x1,y1,z1,poly->verts[1]);
    load_vert(x2,y2,z2,poly->verts[2]);
    w0=poly->vertws[0];
    w1=poly->vertws[1];
    w2=poly->vertws[2];
      
    if (!gfx_bounds_test(x0,y0,w,h) 
      && !gfx_bounds_test(x1,y1,w,h)
      && !gfx_bounds_test(x2,y2,w,h))
      continue;
    
    xmin = (int)min(min(x0,x1),x2);
    xmax = (int)max(max(x0,x1),x2);
    ymin = (int)min(min(y0,y1),y2);
    ymax = (int)max(max(y0,y1),y2);
    
    x10 = x1 - x0; // v1 - v0
    y10 = y1 - y0; 
    x21 = x2 - x1; // v2 - v1
    y21 = y2 - y1; 
    x02 = x0 - x2; // v0 - v2
    y02 = y0 - y2; 
    
    det[0] = x0*y1 - x1*y0;
    det[1] = x1*y2 - x2*y1;
    det[2] = x2*y0 - x0*y2;    
    //if (det[0]+det[1]+det[2]<0)
    //  continue;
    
    #define g_nd(vx,vy) (x10*vy - y10*vx + det[0])
    #define a_nd(vx,vy) (x21*vy - y21*vx + det[1])
    #define b_nd(vx,vy) (x02*vy - y02*vx + det[2])
    
    ad = a_nd(x0,y0);
    bd = b_nd(x1,y1);
    gd = g_nd(x2,y2);
    a = a_nd(xmin,ymax)/ad;
	b = b_nd(xmin,ymax)/bd;
	g = g_nd(xmin,ymax)/gd;
	
    diffx = xmax - xmin;
	x10 /= ad; 
	y10 /= ad;
	x21 /= bd; 
	y21 /= bd;
	x02 /= gd; 
	y02 /= gd;
    x10 -= (y10*diffx);
    x21 -= (y21*diffx);
    x02 -= (y02*diffx);
    	
    for (y=ymax;y>ymin;y--) { // top to bottom
      for (x=xmin;x<xmax;x++) { // left to right            
        if (a >= -0.01 && b >= -0.01 && g >= -0.01) {
          z = ((z0*(a/w0)) + 
               (z1*(b/w1)) + 
               (z2*(g/w2))) /
               ((a/w0)+(b/w1)+(g/w2));
 
          if (gfx_bounds_test(x, y, w, h)) {
            idx = gfx_pixel_idx(x, y, w, h)/3;
            if (!z_buf[idx].draw_count || (z >= 0 && z_buf[idx].z >= z)) {
              z_buf[idx].z = z;
              z_buf[idx].poly_id = poly_ids[i];
			  z_buf[idx].draw_count++;
            }
          }
        }
        a -= y21;
        b -= y02;
        g -= y10;
      }
      a -= x21;  
      b -= x02;
      g -= x10;
    }
  }
}

void draw_polys(poly_id *poly_ids, fpoly *polys, 
                int poly_count, /*pshader_t shader,*/ 
                int w, int h, uint8_t *pixels) {
  int i, ii, idx, x, y;
  fpoly *poly;
  float x0,y0,z0,x1,y1,z1,x2,y2,z2,w0,w1,w2;
  double x10,x21,x02,y10,y21,y02;
  double ad,bd,gd;
  double a,b,g;
  float f_min, f_max;
  int xmin,ymin,xmax,ymax;
  int xmin_idx, xmax_idx, xm_idx, ym_idx, ymin_idx, ymax_idx;
  int diffx;
  double det[3];
  float z;
  int check;
  
  for (i=0;i<poly_count;i++) {
    poly = &polys[i];
    
    #define load_vert(vx,vy,vz,v) vx=v.x;vy=v.y;vz=v.z;
    load_vert(x0,y0,z0,poly->verts[0]);
    load_vert(x1,y1,z1,poly->verts[1]);
    load_vert(x2,y2,z2,poly->verts[2]);
    w0=poly->vertws[0];
    w1=poly->vertws[1];
    w2=poly->vertws[2];
      
    if (!gfx_bounds_test(x0,y0,w,h) 
      && !gfx_bounds_test(x1,y1,w,h)
      && !gfx_bounds_test(x2,y2,w,h))
      continue;
    
    xmin = (int)min(min(x0,x1),x2);
    xmax = (int)max(max(x0,x1),x2);
    ymin = (int)min(min(y0,y1),y2);
    ymax = (int)max(max(y0,y1),y2);
    
    x10 = x1 - x0; // v1 - v0
    y10 = y1 - y0; 
    x21 = x2 - x1; // v2 - v1
    y21 = y2 - y1; 
    x02 = x0 - x2; // v0 - v2
    y02 = y0 - y2; 
    
    det[0] = x0*y1 - x1*y0;
    det[1] = x1*y2 - x2*y1;
    det[2] = x2*y0 - x0*y2;    
    
    //if (det[0]+det[1]+det[2]<0)
    //  continue;
    
    #define g_nd(vx,vy) (x10*vy - y10*vx + det[0])
    #define a_nd(vx,vy) (x21*vy - y21*vx + det[1])
    #define b_nd(vx,vy) (x02*vy - y02*vx + det[2])
    
    ad = a_nd(x0,y0);
    bd = b_nd(x1,y1);
    gd = g_nd(x2,y2);
    a = a_nd(xmin,ymax)/ad;
	b = b_nd(xmin,ymax)/bd;
	g = g_nd(xmin,ymax)/gd;
	
    diffx = xmax - xmin;
	x10 /= ad; 
	y10 /= ad;
	x21 /= bd; 
	y21 /= bd;
	x02 /= gd; 
	y02 /= gd;
    x10 -= (y10*diffx);
    x21 -= (y21*diffx);
    x02 -= (y02*diffx);
    	
    for (y=ymax;y>ymin;y--) { // top to bottom
      for (x=xmin;x<xmax;x++) { // left to right            
        if (a >= -0.02 && b >= -0.02 && g >= -0.02) {
          z = ((z0*(a/w0)) + 
               (z1*(b/w1)) + 
               (z2*(g/w2))) /
               ((a/w0)+(b/w1)+(g/w2));
 
          if (gfx_bounds_test(x, y, w, h)) {
            idx = gfx_pixel_idx(x,y,w,h);
            pixels[idx] = 0xFF - ((int)(z/32) & 0xFF);
            pixels[idx+1] = 0xFF - ((int)(z/32) & 0xFF);
            pixels[idx+2] = 0xFF - ((int)(z/32) & 0xFF);
          }
        }
        a -= y21;
        b -= y02;
        g -= y10;
      }
      a -= x21;  
      b -= x02;
      g -= x10;
    }
  }
}

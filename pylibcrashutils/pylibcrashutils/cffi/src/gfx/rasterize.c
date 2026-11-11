/**
 * software rasterization for transformed polys
 * 
 * currently includes only functions for rendering to the z-buffer
 */
#include "rasterize.h"

#define min(a,b) (a)<(b)?(a):(b)
#define max(a,b) (a)>(b)?(a):(b)
#define minmax_3(mn,mx,a,b,c) \
mn=a;mx=b; \
if(b<mn){mn=b;mx=a;} \
if(c<mn)mn=c; \
else if(c>mx)mx=c;

#define print_poly(poly) \
for (vi=0;vi<3;vi++) { \
  printf("vert %i: (x: %f, y: %f, z: %f)\\n", vi, \
    (poly)->verts[vi].x, (poly)->verts[vi].y, (poly)->verts[vi].z); \
}

int bitset_count[8] = { 0, 1, 1, 2, 1, 2, 2, 3 };
int bitset_vert_idx[8] = { -1, 2, 1, 0, 0, 1, 2, -1 };
int bitset_inside_idxs[8][2] = \
  { { -1, -1 }, { 2, -1 }, { 1, -1 }, { 1, 2 }, 
    {  0, -1 }, { 0,  2 }, { 0,  1 }, { -1, -1 } };
int bitset_others_idxs[8][2] = \
  { { -1, -1 }, { 0, 1 }, { 0, 2 }, { 1, 2 }, 
    {  1,  2 }, { 0, 2 }, { 0, 1 }, { -1, -1 } };
float edge_values[7] = { -999, -999, -1.0, 1.0, -1.0, 1.0, 1.0 };

fpnt clip_ul, clip_lr;
fpnt edge_n[6];
fpnt edge_p[6];
z_struct z_buf[512*512];

/**
 * determines which verts of a poly are inside and outside of a face of
 * the viewing frustum 
 */
inline static int test_poly(fpoly *poly, int edge) {
  int i, bits;
  fpnt *vert, *vertuvw;
  
  #define test_poly_case(c,test) \
  case c: \
    for (i=0;i<3;i++) { \
      bits <<= 1; \
      vert = &poly->verts[i]; \
      vertuvw = &poly->vertuvws[i]; \
      if (test) \
        bits |= 1; \
    } \
    break;
    
  bits = 0;
  switch (edge) {
  test_poly_case(0, (int)vert->x >= (int)(clip_ul.x*(vert->z/clip_ul.z)))
  test_poly_case(1, (int)vert->x <= (int)(clip_lr.x*(vert->z/clip_ul.z)))
  test_poly_case(2, (int)vert->y >= (int)(clip_ul.y*(vert->z/clip_ul.z)))
  test_poly_case(3, (int)vert->y <= (int)(clip_lr.y*(vert->z/clip_ul.z)))
  test_poly_case(4, (int)vert->z >= (int)clip_ul.z)
  test_poly_case(5, (int)vert->z <= (int)clip_lr.z) 
  test_poly_case(6, vertuvw->z >= 1.0)
  }
  return bits;
}

/**
 * determines if a poly is valid 
 * 
 * a poly is valid if no 2 vertices are the same and no component is a
 * NaN value
 */
inline static int is_valid_poly(fpoly *poly) {
  int i;
  for (i=0;i<3;i++) {
    if (poly->verts[i].x == poly->verts[(i+2)%3].x &&
        poly->verts[i].y == poly->verts[(i+2)%3].y)
      return 0;
    if ((poly->verts[i].x != poly->verts[i].x) ||
        (poly->verts[i].y != poly->verts[i].y))
      return 0;
  }
  return 1;
}

/** 
 * unprojects a poly from screen to (rotated) view coordinates
 */
inline static void unproject_poly(fpoly *poly) {
  int i;
  fpnt *vert, *vertuvw;
  
  for (i=0;i<3;i++) { 
    vert = &poly->verts[i];
    vertuvw = &poly->vertuvws[i];
    vert->x = ((vert->x * clip_lr.x) / vertuvw->z)*65536;
    vert->y = ((vert->y * clip_lr.y) / vertuvw->z)*65536;
  }
}

/**
 * reprojects a poly from (rotated) view coordinates back to screen
 * coordinates
 */
inline static void reproject_poly(fpoly *poly) {
  int i;
  fpnt *vert, *vertuvw;
  
  for (i=0;i<3;i++) {
    vert = &poly->verts[i];
    vertuvw = &poly->vertuvws[i];
    vert->x = ((vert->x/65536) * vertuvw->z)/clip_lr.x;
    vert->y = ((vert->y/65536) * vertuvw->z)/clip_lr.y;
  }
}
  
/**
 * finds the first point of intersection between a poly edge and the
 * viewing frustum, if any
 * 
 * poly: poly with edge
 * i0: index of edge's first vertex (in the poly)
 * i1: index of edge's second vertex (in the poly)
 * edge: index of viewing frustum face
 * clipped: the point of intersection, if any
 * clipped_uvw: uvw coords for the point of intersection
 * 
 * returns: 1 if intersection
 *          0 if no intersection
 */
inline static int frustum_intersection(fpoly *poly, int i0, int i1, 
                                       int edge, 
                                       fpnt *clipped, fpnt *clipped_uvw) {
  int i;
  float depth, scale;
  fpnt n, p, l;
  float w, h, d;
  fpnt *p0, *p1;
  
  static int setup = 0;
 
  depth = (clip_lr.z - clip_ul.z);
  scale = ((clip_lr.z/clip_ul.z)-1)/(2*depth);
  w = clip_lr.x - clip_ul.x;
  h = clip_lr.y - clip_ul.y; 
  if (!setup) {
    for (i=0;i<6;i++) {
      edge_p[i].x = 0; edge_p[i].y = 0;
      edge_p[i].z = clip_ul.z;
      edge_n[i].x = 0; edge_n[i].y = 0;
    }
    edge_p[0].x = clip_ul.x; edge_p[0].y = clip_lr.y;
    edge_p[1].x = clip_lr.x; edge_p[1].y = clip_ul.y;
    edge_p[2].x = clip_ul.x; edge_p[2].y = clip_ul.y;
    edge_p[3].x = clip_lr.x; edge_p[3].y = clip_lr.y;
    edge_p[5].z = clip_lr.z;
    edge_n[0].x = -1; 
    edge_n[1].x =  1;
    edge_n[2].y = -1;
    edge_n[3].y =  1;
    edge_n[0].z = -w*scale;
    edge_n[1].z = -w*scale;
    edge_n[2].z = -h*scale;
    edge_n[3].z = -h*scale;
    edge_n[4].z = -1;
    edge_n[5].z = 1;
    setup = 1;
  }

  n = edge_n[edge];
  p = edge_p[edge];
  p0 = &poly->verts[i0]; 
  p1 = &poly->verts[i1];
  l.x = p1->x - p0->x;
  l.y = p1->y - p0->y;
  l.z = p1->z - p0->z;
  
  d = ((p.x-p0->x)*n.x + (p.y-p0->y)*n.y + (p.z-p0->z)*n.z) /
      (l.x*n.x + l.y*n.y + l.z*n.z);
  if (d >= 0 && d <= 1) {
    clipped->x = p0->x + d*l.x;
    clipped->y = p0->y + d*l.y;
    clipped->z = p0->z + d*l.z;
    clipped_uvw->z = poly->vertuvws[i0].z + \
                  d*(poly->vertuvws[i1].z - poly->vertuvws[i0].z);
    return 1;
  }
  return 0;
}
   
/** 
 * determines if a poly is back-facing
 * 
 * returns: 1 if the poly is back-facing
 *          0 if not
 */ 
inline static int backface_cull_poly(fpoly *poly) {
  fpnt *v0, *v1, *v2;
  fpnt v10, v20, n;
  float d;
  
  v0 = &poly->verts[0];
  v1 = &poly->verts[1];
  v2 = &poly->verts[2];

  v10.x = v1->x - v0->x;
  v10.y = v1->y - v0->y;
  v10.z = v1->z - v0->z;
  v20.x = v2->x - v0->x;
  v20.y = v2->y - v0->y;
  v20.z = v2->z - v0->z;
  
  n.x = v10.y*v20.z - v10.z*v20.y;
  n.y = v10.z*v20.x - v10.x*v20.z;
  n.z = v10.x*v20.y - v10.y*v20.x;
  
  d = ((v0->x*n.x) + (v0->y*n.y) + (v0->z*n.z));
  return d >= 0;
}

/**
 * clips a poly at the first frustum face with which it intersects, if
 * any. 
 *
 * the result polys themselves may still intersect the frustum; 
 * therefore it may be necessary to recursively call this function on 
 * results to get the complete set of polys (i.e. triangles) which cover
 * the original 'clipped poly'
 *
 * returns: -1 if poly is rejected
 *           0 if no clipping necessary
 *           1 if poly is clipped
 */
inline static int clip_poly(fpoly *src_poly, fpoly *dst_polys,
                            int *poly_count) {
  int i, ii, idx, bits, count, vidx;
  fpnt new_verts[4], new_vertuvws[4];
  fpnt new_vert, new_vertuvw;
  int new_vert_count;
  fpoly *new_poly;
  int sect;
  
  #define append_new_vert(v,u) \
  new_verts[new_vert_count] = v; \
  new_vertuvws[new_vert_count] = u; \
  new_vert_count++;
  #define append_new_poly(o) \
  new_poly = &dst_polys[(*poly_count)++]; \
  for (ii=0;ii<3;ii++) { \
    new_poly->verts[ii] = new_verts[ii+o]; \
    new_poly->vertuvws[ii] = new_vertuvws[ii+o]; \
  }
  
  if (!is_valid_poly(src_poly)) return -1;

  *poly_count = 0;
  new_vert_count = 0;
  for (i=0;i<5;i++) {
    bits = test_poly(src_poly, i);
    count = bitset_count[bits];
    if (count == 3) continue; // if all 3 on inside, then try next edge
    else if (count == 0) return -1; // all outside, so reject
    for (ii=0;ii<2;ii++) {
      idx = bitset_inside_idxs[bits][ii];
      if (idx == -1) break;
      append_new_vert(src_poly->verts[idx], src_poly->vertuvws[idx]);
    }
    vidx = bitset_vert_idx[bits];
    for (ii=0;ii<2;ii++) {
      idx = bitset_others_idxs[bits][ii];
      sect = frustum_intersection(src_poly, vidx, idx, i, &new_vert, &new_vertuvw);
      append_new_vert(new_vert, new_vertuvw);
    }
    append_new_poly(0);
    if (new_vert_count > 3) {
      append_new_poly(1);
    }
    return 1;
  }
  return 0;
}
    
/**
 * clips polys at viewing frustum faces
 */
void clip_polys(poly_id *dst_ids, fpoly *dst_polys, 
                poly_id *src_ids, fpoly *src_polys,
                int *poly_count) {
  int i, ii, idx, top, vi;
  int count, dst_count;
  int res;
  fpoly poly_stack[0x4000];
  poly_id id_stack[0x4000];
  fpoly poly;
  poly_id poly_id;
  fpoly clipped[2];
  int count_map[0x8000];
  
  for (top=0,i=(*poly_count)-1;i>=0;i--,top++) {
    poly_stack[top] = src_polys[i];
    id_stack[top] = src_ids[i];
    unproject_poly(&poly_stack[top]);
    count_map[poly_id_val(src_ids[i])] = 0;
  }
  dst_count = 0;
  while (top) {
    top--;
    poly = poly_stack[top];
    poly_id = id_stack[top];
    count_map[poly_id_val(poly_id)]++;
    if (count_map[poly_id_val(poly_id)] > 16) continue; // discard the poly if we've tried too many times
    // if (backface_cull_poly(&poly)) continue;
    res = clip_poly(&poly, &clipped, &count);
    if (res == 0) {
      dst_polys[dst_count] = poly;
      dst_ids[dst_count] = poly_id;
      dst_count++;
    }
    else if (res == 1) {
      for (i=0;i<count;i++) {
        poly_stack[top] = clipped[i];
        id_stack[top] = poly_id;
        top++;
      }
    }
  }
  for (i=0;i<dst_count;i++)
    reproject_poly(&dst_polys[i]);
  *poly_count = dst_count;
}  

#ifndef GFX_RASTERIZE_BARYCENTRIC

#define gfx_edge_iter_init_left(edge) \
edge->count = 2; \
edge->height = v1->y - v0->y; \
edge->idx = -1; \
edge->y = 0; \
edge->verts[0] = v0; edge->verts[1] = v1; edge->verts[2] = v2; \
gfx_edge_iter_next_idx(edge);
#define gfx_edge_iter_init_right(edge) \
edge->count = 1; \
edge->height = v2->y - v0->y; \
edge->idx = -1; \
edge->y = 0; \
edge->verts[0] = v0; edge->verts[1] = v2;\
gfx_edge_iter_next_idx(edge);

#define gfx_edge_iter_next_idx(edge) \
if (++edge->idx >= edge->count) break; \
v0 = edge->verts[edge->idx]; v1 = edge->verts[edge->idx+1]; \
edge->height = v1->y - v0->y; \
edge->dx = (float)(v1->x - v0->x) / edge->height; \
edge->dz = (float)(v1->z - v0->z) / edge->height; \
edge->x = v0->x; \
edge->y = 0; \
edge->z = v0->z;
#define gfx_edge_iter_next_row(edge) \
edge->x += edge->dx; \
edge->y += 1; \
edge->z += edge->dz; 
#endif

/**
 * rasterizes an array of polys to the z-buffer
 * 
 * if GFX_RASTERIZE_BARYCENTRIC is defined this will use barycentric
 * coordinates to do the rasterization (likely slower)
 * 
 * its is recommended that polys are clipped to the viewing frustum 
 * prior to calling this function
 * 
 * poly_ids: ids of polys
 * polys: polys
 * poly_count: number of polys
 * w: length of a z buffer row
 * h: number of z-buffer rows
 */
void draw_polys_zbuf(poly_id *poly_ids, fpoly *polys, 
                     int poly_count, 
                     int w, int h) {
  int i, idx, x, y;
  fpoly *poly;
  int xmin,ymin,xmax,ymax;
#ifndef GFX_RASTERIZE_BARYCENTRIC
  double w0,w1,w2;
  int height;
  float winding;
  fpntw verts[3], *v0, *v1, *v2;
  int vert_count;
  gfx_edge_iter e1, e2, *left, *right;
  z_struct *zs;
  float z,dz;
  float zmin,zmax;
#else
  double x0,y0,z0,x1,y1,z1,x2,y2,z2,w0,w1,w2;
  double x10,x21,x02,y10,y21,y02;
  double ad,bd,gd;
  double a,b,g;
  int diffx;
  double det[3];
  double z,wc;
#endif

  for (i=0;i<poly_count;i++) {
    poly = &polys[i];
   
#ifndef GFX_RASTERIZE_BARYCENTRIC
    vert_count=0;
    #define load_vert(d,s,suvw) d=&verts[vert_count++]; \
    d->x=(s.x+1)*(w/2);d->y=(1-s.y)*(h/2);d->z=s.z; \
    d->w=suvw.z;
    load_vert(v0,poly->verts[0],poly->vertuvws[0]);
    load_vert(v1,poly->verts[1],poly->vertuvws[1]);
    load_vert(v2,poly->verts[2],poly->vertuvws[2]);
    w0 = poly->vertuvws[0].z;
    w1 = poly->vertuvws[1].z;
    w2 = poly->vertuvws[2].z;
    if(v0->y > v1->y) { fpnt* v = v0; v0 = v1; v1 = v; }
    if(v0->y > v2->y) { fpnt* v = v0; v0 = v2; v2 = v; }
    if(v1->y > v2->y) { fpnt* v = v1; v1 = v2; v2 = v; }
    height = v2->y - v0->y;
    winding = (((float)(v1->y - v0->y) / height) * (v2->x - v0->x)) 
              + (v0->x - v1->x);
    if (winding == 0) continue;
    left = &e1; right = &e2;
    gfx_edge_iter_init_left(left);
    gfx_edge_iter_init_right(right);
    if (winding < 0) {
      gfx_edge_iter *tmp = left; left = right; right = tmp;
    }
    ymin = v0->y; ymax = v2->y;
    for (y=ymin;y<ymax;y++) {
      if (left->y == left->height) { gfx_edge_iter_next_idx(left); }
      if (right->y == right->height) { gfx_edge_iter_next_idx(right); }
      xmin = (int)left->x; xmax = (int)right->x;
      zmin = left->z; zmax = right->z;
      dz = (zmax - zmin)/(xmax - xmin);
      z = zmin;
      for (x=xmin;x<xmax;x++) {
        if (gfx_bounds_test(x, y, w, h)) {
          idx = gfx_pixel_idx(x, y, w, h)/3;
          zs = &z_buf[idx];
          if (z > 0.0 && (!zs->draw_count || zs->z >= z)) {
            zs->z = z;
            zs->poly_id = poly_ids[i];
            zs->draw_count++;
          }
        }
        z += dz;
      }
      gfx_edge_iter_next_row(left);
      gfx_edge_iter_next_row(right);
    }
        
#else
    #define load_vert(vx,vy,vz,v) vx=(v.x+1)*(w/2);vy=(1-v.y)*(h/2);vz=v.z;
    load_vert(x0,y0,z0,poly->verts[0]);
    load_vert(x1,y1,z1,poly->verts[1]);
    load_vert(x2,y2,z2,poly->verts[2]);
    
    w0=poly->vertuvws[0].z;
    w1=poly->vertuvws[1].z;
    w2=poly->vertuvws[2].z;

	if ((w0 < 0 || w1 < 0 || w2 < 0))
	  continue;
	if ((z0 < 0 || z1 < 0 || z2 < 0))
	  continue;
	//if (w0 < 0) { w0 = 0.01; }
	//if (w1 < 0) { w1 = 0.01; }
	//if (w2 < 0) { w2 = 0.01; }
	    
    x10 = x1 - x0; // v1 - v0
    y10 = y1 - y0; 
    x21 = x2 - x1; // v2 - v1
    y21 = y2 - y1; 
    x02 = x0 - x2; // v0 - v2
    y02 = y0 - y2; 
    
    xmin = (int)min(min(x0,x1),x2);
    xmax = (int)max(max(x0,x1),x2);
    ymin = (int)min(min(y0,y1),y2);
    ymax = (int)max(max(y0,y1),y2);
    
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
          //wc = (a+b+g)/((a/w0)+(b/w1)+(g/w2));
          //if (wc < 0.0) continue;
          
          z = ((z0*(a/w0)) + 
               (z1*(b/w1)) + 
               (z2*(g/w2))) /
               ((a/w0)+(b/w1)+(g/w2));
 
          if (gfx_bounds_test(x, y, w, h)) {
            idx = gfx_pixel_idx(x, y, w, h)/3;
            if (z > 0.0 && (!z_buf[idx].draw_count || z_buf[idx].z >= z)) {
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
#endif
  }
}


int clipped_edge;
/**
 * clips a poly at the first viewport edge with which it intersects, if
 * any. 
 *
 * the result polys themselves may still intersect the viewport; 
 * therefore it may be necessary to recursively call this function on 
 * results to get the complete set of polys (i.e. triangles) which cover
 * the original 'clipped poly'
 *
 * returns: -1 if poly is rejected
 *           0 if no clipping necessary
 *           1 if poly is clipped
 */

/*
=========== VVVVV OLD CODE VVVVV ===========
inline static int clip_poly(fpoly *src_poly, fpoly *dst_polys,
                             int *poly_count) {
  int i, ii, idx, bits, count;
  fpnt new_verts[4], new_vertuvws[4];
  int new_vert_count;
  fpnt *vert, *other, *new_vert;
  fpnt *vertuvw, *otheruvw, *new_vertuvw;
  float val, t, x, y, z, w, tmp;
  fpoly *new_poly;
  int vi;
  
  *poly_count = 0;
  for (i=0;i<1;i++) {
    if (i==1) continue; // skip far clipping for now
    clipped_edge=i;
    bits = test_poly(src_poly, i);
    count = bitset_count[bits];
    if (count == 3) continue; // if all 3 on inside, then try next edge
    else if (count == 0) return -1; // all outside, so reject
    new_vert_count = 0;
    for (ii=0;ii<2;ii++) {
      idx = bitset_inside_idxs[bits][ii];
      if (idx == -1) break;
      new_verts[new_vert_count] = src_poly->verts[idx];
      new_vertuvws[new_vert_count] = src_poly->vertuvws[idx];
      new_vert_count++;
    }
    val = edge_values[i];
    if (i >= 0 && i < 2)
      unproject_poly(src_poly);
    vert = &src_poly->verts[bitset_vert_idx[bits]];
    vertuvw = &src_poly->vertuvws[bitset_vert_idx[bits]];
    for (ii=0;ii<2;ii++) { 
      idx = bitset_others_idxs[bits][ii];
      other = &src_poly->verts[idx];
      otheruvw = &src_poly->vertuvws[idx];
      if (i >= 0 && i < 2)
        t = (val-vert->z)/(other->z-vert->z);
      else if (i < 4)
        t = (val-vert->x)/(other->x-vert->x);
      else if (i < 6)
        t = (val-vert->y)/(other->y-vert->y);
      else if (i == 6)
        t = (val-vertuvw->z)/(otheruvw->z-vertuvw->z);  // w
      if (t < 0 || t > 1) continue;
      x = vert->x + t*(other->x-vert->x);
      y = vert->y + t*(other->y-vert->y);
      z = vert->z + t*(other->z-vert->z);
      w = vertuvw->z + t*(otheruvw->z-vertuvw->z);
      new_vert = &new_verts[new_vert_count];
      new_vertuvw = &new_vertuvws[new_vert_count];
      new_vert->x = x;
      new_vert->y = y;
      new_vert->z = z;
      new_vertuvw->z = w;
      new_vert_count++;
    }
    new_poly = &dst_polys[(*poly_count)];
    for (ii=0;ii<3;ii++) {
      new_poly->verts[ii] = new_verts[ii];
      new_poly->vertuvws[ii] = new_vertuvws[ii];
    }
    if (is_valid_poly(new_poly)) (*poly_count)++; 
    if (new_vert_count > 3) {
      new_poly = &dst_polys[(*poly_count)];
      for (ii=0;ii<3;ii++) {
        new_poly->verts[ii] = new_verts[ii+1];
        new_poly->vertuvws[ii] = new_vertuvws[ii+1];
      }
      if (is_valid_poly(new_poly)) (*poly_count)++; 
    }
    if (i >= 0 && i < 2) {
      for (ii=0;ii<(*poly_count);ii++)
        reproject_poly(&dst_polys[ii]);
      reproject_poly(src_poly);
    } 
    if ((*poly_count) == 0) return -1;
    // if (*poly_count == 1) {
    //   for (ii=0;ii<3;ii++) {
    //     if (dst_polys[0].verts[ii].x != src_poly->verts[ii].x ||
    //       dst_polys[0].verts[ii].y != src_poly->verts[ii].y)
    //       break;
    //   }
    //   if (ii == 3) return 0;
    // }
    return 1;
  }
  return 0;
}
*/
/*
  vert attributes:
    - normalized/unnormalized?
    - uncentered/centered?
    - projected/unprojected?
    - fixed point/floating point?
    - shifted/unshifted? (i.e. scaled for fixed point precision)
    
    - normalized/unnormalized:
      - normalized: in the range   (-1.0, -1.0) to (1.0, 1.0) for centered, 
                                      (0,    0) to (2.0, 2.0) for uncentered.
      - unnormalized: in the range (-w/2, -h/2) to (w/2, h/2) for centered.
                                      (0,    0) to (w, h) for uncentered.
      - conversion: multiply for n->u, divide for u->n, 
                    by (w/2, h/2) if no change in centering
                    else add (-1.0,-1.0) for uncentered, 
                               (1.0,1.0) for centered
                    - before the mult if n->u
                    - else after the division if u->n

    - projected/unprojected
      - projected: have been multiplied by w coordinates (ofsz / vert.z)
      - unprojected: have not been multiplied by w coordinates
  
      - conversion: p->u: divide by w
                    u->p: multiply by w
                    
    - shifted/unshifted
      - shifted: need to divide by some power of 2 for the actual 
        representative value
      - unshifted: directly represented by its values
      
      - conversion: s->u: divide by power of 2, 
                    u->s: multiply by power of 2
  
  
  given w=512, h=256
  ofsx = 512/2, ofsy = 256/2, ofsz = 288
  
  for shifted unnormalized centered unprojected u_vert,
  to get unnormalized unshifted centered projected s_vert:
  
  s_vert.x = ((u_vert.x / 65536) * ofsz)
  s_vert.y = ((u_vert.y / 65536) * ofsz)
  
  if s_vert = (-ofsx, -ofsy)
  
  -ofsx = ((u_vert.x / 65536) * ofsz)
  -ofsy = ((u_vert.y / 65536) * ofsz)
  
  u_vert.x = (-ofsx/ofsz) * 65536
  u_vert.y = (-ofsy/ofsz) * 65536
*/

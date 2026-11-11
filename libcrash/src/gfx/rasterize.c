/**
 * Software rasterizer for screen coordinate geometry produced 
 * by functions in transform.c
 */ 

#include "gfx.h"

#define gfx_bounds_test(x,y,w,h) (((x) > (0)) && ((y) > (0)) \
                               && ((x) < (w)) && ((y) < (h)))
#define gfx_pixel_idx(x,y,w,h) ((((y)*(w))+(x))*3)


static const int lerp_res = 200;
static const int z_scale = 0x10;

void draw_polys_wireframe(poly_id *poly_ids, fpoly *polys, 
                          uint32_t poly_count, pshader_t shader, 
                          uint32_t w, uint32_t h, uint8_t *pixels) {
  int i, ii, iii, idx;
  fpoly *poly;
  vec32 diff[3];
  uint32_t vcol[3];
  uint8_t p_color[4];
  pnt32 pnt;
  
  for (i=0;i<poly_count;i++) {
    poly = polys++;
   
    if (poly->verts[0].z < 0 || 
        poly->verts[1].z < 0 || 
        poly->verts[2].z < 0) 
      continue; // should this be in a separate clipping stage?
   
    vcol[0] = poly->verts[0].z/z_scale;
    vcol[1] = poly->verts[1].z/z_scale;
    vcol[2] = poly->verts[2].z/z_scale;
    
    diff[0].x = poly->verts[1].x - poly->verts[0].x, // v1 - v0
    diff[0].y = poly->verts[1].y - poly->verts[0].y, 
    diff[0].z = vcol[1] - vcol[0]; 
    diff[1].x = poly->verts[2].x - poly->verts[1].x; // v2 - v1
    diff[1].y = poly->verts[2].y - poly->verts[1].y;
    diff[1].z = vcol[2] - vcol[1];
    diff[2].x = poly->verts[0].x - poly->verts[2].x; // v0 - v2
    diff[2].y = poly->verts[0].y - poly->verts[2].y;    
    diff[2].z = vcol[0] - vcol[2];                     
                    
    for (ii=0;ii<lerp_res;ii++) {
      for (iii=0;iii<3;iii++) {
        pnt.x = poly->verts[iii].x+((float)(ii*diff[iii].x)/lerp_res);
        pnt.y = poly->verts[iii].y+((float)(ii*diff[iii].y)/lerp_res);
        pnt.z = vcol[iii]+((float)(ii*diff[iii].z)/lerp_res);
        
        if (!gfx_bounds_test(pnt.x, pnt.y, w, h))
          continue;
        
        idx = gfx_pixel_idx(pnt.x, pnt.y, w, h);
  
        p_color[0] = 255;
        p_color[1] = 255;
        p_color[2] = 255;
        if (shader) {
          shader(poly_ids[i], *poly, pnt, &p_color);
        }
        pixels[idx] = p_color[0];
        pixels[idx+1] = p_color[1];
        pixels[idx+2] = p_color[2];
      }
    }
  }  
}

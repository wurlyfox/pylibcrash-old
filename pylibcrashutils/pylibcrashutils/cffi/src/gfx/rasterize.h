#ifndef RASTERIZE_H
#define RASTERIZE_H

#include "gfx.h"

#define gfx_bounds_test(x,y,w,h) (((x) >= (0)) && ((y) >= (0)) \
                               && ((x) < (w)) && ((y) < (h)))
#define gfx_pixel_idx(x,y,w,h) ((((y)*(w))+(x))*3)

typedef struct {
  float z;
  poly_id poly_id;
  int draw_count;
} z_struct;
typedef struct {
  float x;
  float y;
  float z;
  float w;
} fpntw;
typedef struct {
  fpntw *verts[3];
  int count;
  int height;
  int idx;
  float dx;
  float dz;
  float dw;
  float x;
  int y;
  float z;
  float w;
} gfx_edge_iter;
extern void draw_polys_zbuf(poly_id *poly_ids, fpoly *polys, 
                            int poly_count, int w, int h);
extern void clip_polys(poly_id *ids_clipped, fpoly *polys_clipped, 
                       poly_id *poly_ids, fpoly *polys, 
                       int *poly_count);

#endif

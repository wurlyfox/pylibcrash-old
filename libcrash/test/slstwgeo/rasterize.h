#ifndef RASTERIZE_H
#define RASTERIZE_H

#include "gfx.h"

typedef struct {
  float z;
  poly_id poly_id;
  int draw_count;
} z_struct;

extern void draw_polys_zbuf(poly_id *poly_ids, fpoly *polys, 
                            int poly_count, /*pshader_t shader,*/ 
                            int w, int h, z_struct *z_buf);

extern void draw_polys(poly_id *poly_ids, fpoly *polys, 
                       int poly_count, /*pshader_t shader,*/ 
                       int w, int h, uint8_t *pixels);
#endif

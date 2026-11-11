#include "gfx.h"
#include "rasterize.h"

#include "pcsx/soft.h"

/**
 * Initializes maps and buffers used to compute polygon visibility.
 */
fpoly *poly_map[0x8000];
int draw_count_map[0x8000];
poly_id poly_id_buf[8192], ids_clipped[8192];
fpoly poly_buf[8192], polys_clipped[8192];

static inline void init_vis_maps(poly_id *poly_ids, fpoly *polys, 
                                 int poly_count) {
  int i;
  poly_id poly_id;
  int poly_id_val;
  
  memset(&poly_map, 0, sizeof(poly_map));
  memset(&draw_count_map, 0, sizeof(draw_count_map));
  memcpy(&poly_id_buf, poly_ids, sizeof(poly_id)*poly_count);
  memcpy(&poly_buf, polys, sizeof(fpoly)*poly_count);
  for (i=0;i<poly_count;i++) {
    poly_id = poly_id_buf[i];
    poly_id_val = poly_id_val(poly_id);
    poly_map[poly_id_val] = &poly_buf[i];
  }
}

/**
 * Filters polys/poly ids by visibility (neither occluded nor clipped)
 * Can only be used after polys have been projected.
 * 
 * Uses custom implementation for software rasterization to the z-buffer.
 */
extern fpnt clip_ul, clip_lr;
extern z_struct z_buf[512*512];
static void compute_visible_polys_plcu(poly_id *poly_ids, fpoly *polys,
                                       int *poly_count,
                                       int w, int h, float near) {
  int i, z_buf_len;
  fpoly *poly;
  poly_id poly_id;
  int poly_id_val;
  int draw_count;
  z_struct *zs;
  
  init_vis_maps(poly_ids, polys, *poly_count);
  memset(&z_buf, 0, sizeof(z_buf));
    
  clip_ul.x = -w/2;
  clip_ul.y = -h/2;
  clip_ul.z = near;
  clip_lr.x = w/2;
  clip_lr.y = h/2;
  clip_lr.z = 30000; // no far value passed yet
    
  // clip polys first, otherwise wastes rasterize time
  clip_polys(ids_clipped, polys_clipped, poly_ids, polys, poly_count);
  draw_polys_zbuf(ids_clipped, polys_clipped, *poly_count, w, h);
  //draw_polys_zbuf(poly_ids, polys, *poly_count, w, h);
    
  *poly_count = 0;
  z_buf_len = w*h;
  for (i=0;i<z_buf_len;i++) {
    zs = &z_buf[i];
    if (!zs->draw_count) continue;
    poly_id = zs->poly_id;
    poly_id_val = poly_id_val(poly_id);
    draw_count = draw_count_map[poly_id_val]++;
    if (draw_count != 1) continue; // already drawn more than once or not drawn at least once yet
    if (poly = poly_map[poly_id_val]) { // 
      polys[(*poly_count)] = *poly;
      poly_ids[(*poly_count)++] = poly_id;
    }
  }
}

/**
 * Filters polys/poly ids by visibility (neither occluded nor clipped)
 * Can only be used after polys have been projected.
 * 
 * Uses pcsx for software rasterization to the z-buffer.
 * 
 * Note that poly verts must have integral components. 
 */
extern short lx0, lx1, lx2;
extern short ly0, ly1, ly2;
extern short lz0, lz1, lz2;
extern soft_z psxZbuf[513*1024];
static void compute_visible_polys_pcsx(poly_id *poly_ids, fpoly *polys,
                                       int *poly_count) {
  int i, j;
  fpoly *poly;
  poly_id poly_id;
  int poly_id_val;
  soft_z *zn;
  int draw_count;
  
  init_vis_maps(poly_ids, polys, *poly_count);
  memset(&psxZbuf, 0, sizeof(psxZbuf));
  
  for (i=0;i<*poly_count;i++) {
    poly = &polys[i];
    poly_id = poly_ids[i];
    lx0=poly->verts[0].xi;ly0=poly->verts[0].yi;lz0=poly->verts[0].zi;
    lx1=poly->verts[1].xi;ly1=poly->verts[1].yi;lz1=poly->verts[1].zi;
    lx2=poly->verts[2].xi;ly2=poly->verts[2].yi;lz2=poly->verts[2].zi;
    drawPoly3Z((int)poly_id_val(poly_id));
  }
  
  *poly_count=0;
  for (i=/*256*/0;i</*256+512*/1024;i++) {
    for (j=/*128*/0;j</*384*/512;j++) {
      zn = &psxZbuf[(j<<10)+i];
      if (!zn->count) continue;
      poly_id_val = zn->id;
      poly_id.poly_idx = poly_id_val&0xFFF; 
      poly_id.world_idx = (poly_id_val>>12)&0x7;
      draw_count = draw_count_map[poly_id_val]++;
      if (draw_count > 0) continue; /* unique polys only */
      if (poly = poly_map[poly_id_val]) {
        polys[(*poly_count)] = *poly;
        poly_ids[(*poly_count)++] = poly_id;
      }
    }
  }
}

/**
 * Filters polys/poly ids by visibility (neither occluded nor clipped)
 * Can only be used after polys have been projected.
 * 
 * Uses either custom implementation or pcsx for software rasterization
 * to the z-buffer.
 */
void compute_visible_polys(poly_id *poly_ids, fpoly *polys, 
                           int *poly_count, 
                           int w, int h, float near, int pcsx) {
  if (!pcsx)
    compute_visible_polys_plcu(poly_ids, polys, poly_count, w, h, near);
  else
    compute_visible_polys_pcsx(poly_ids, polys, poly_count);
}

uint32_t *get_zbuf_image(uint32_t *buf, int w, int h, int scale, 
                         int pcsx) {
  int i, size;
  int offset;
  unsigned int color, r, g, b;
  int draw_count, z;
  
  z_struct *zs;
  soft_z *zn;
  
  if (pcsx) {w=1024;h=512;} 
  size = w*h;
  for (i=0;i<size;i++) {
    if (pcsx) {
      zn = &psxZbuf[i];
      z = zn->z;
      draw_count = zn->count;
    }
    else {
      zs = &z_buf[i];
      z = zs->z;
      draw_count = zs->draw_count;
    }
    if (draw_count) { 
      offset = (int)(z / scale);
      r = offset; //+ draw_count*5;
      g = offset; //+ draw_count*7;
      b = offset; //+ draw_count*10;
      color = (r << 24) | (g << 16) | (b << 8) | (255);
    }
    else
      color = 0;
    buf[i] = color;
  }
  
  return buf;
}

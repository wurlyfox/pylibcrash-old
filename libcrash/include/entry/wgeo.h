#ifndef WGEO_H
#define WGEO_H

#include "types.h"
#include "entry.h"

typedef struct {
  uint8_t r;
  uint8_t g;
  uint8_t b;
BITFIELDS_04(
  uint8_t type:1,
  uint8_t semi_trans:2,
  uint8_t :1,
  uint8_t clut_x:4
)
BITFIELDS_07(
  uint32_t region_index:10,
  uint32_t color_mode:2,
  uint32_t segment:2,
  uint32_t offs_x:5,
  uint32_t clut_y:7,
  uint32_t :1,
  uint32_t offs_y:5
)
} wgeo_texinfo;
  
typedef struct {
  int32_t trans_x;
  int32_t trans_y;
  int32_t trans_z;
  uint32_t poly_count;
  uint32_t vert_count;
  uint32_t texinfo_count;
  uint32_t tpag_count;
  uint32_t is_relative;
  eid_t tpags[8];
  wgeo_texinfo texinfos[];
} wgeo_header;

typedef struct {
BITFIELDS_07(
  uint32_t a_idx:12,
  uint32_t b_idx:12,
  uint32_t anim_1:8,
  uint32_t c_idx:12,
  uint32_t tinf_idx:12,
  uint32_t tpag_idx:3,
  uint32_t anim_2:5
) 
} wgeo_polygon;

typedef struct {
  uint8_t r;
  uint8_t g;
  uint8_t b;
  uint8_t z8;
BITFIELDS_05(
  int16_t y:13,
  int16_t z3:3,
  int16_t x:13,
  uint16_t z2:2,
  uint16_t fx:1
)
} wgeo_vertex;

#endif

#ifndef TGEO_H
#define TGEO_H

typedef struct {
BITFIELDS_04(
  uint8_t type:1,
  uint8_t semi_trans:2,
  uint8_t no_cull:1,
  uint8_t clutx:4
)
  uint8_t r;
  uint8_t g;
  uint8_t b;
  eid_t tpage;
BITFIELDS_07(
  uint32_t region_idx:10,
  uint32_t color_mode:2,
  uint32_t segment:2,
  uint32_t offs_x:5,
  uint32_t cluty:7,
  uint32_t :1,
  uint32_t offs_y:5
)
} tgeo_texinfo;

typedef struct {
  uint32_t poly_count;
  uint32_t scale_x;
  uint32_t scale_y;
  uint32_t scale_z;
  uint32_t texinfo_count;
  tgeo_texinfo texinfos[];
} tgeo_header;

typedef struct {
  uint16_t a_idx;  // should be a_offs
  uint16_t b_idx;  // should be b_offs 
  uint16_t c_idx;  // should be c_offs
BITFIELDS_02(
  uint16_t is_flat_shaded:1,
  uint16_t texinfo_idx:15
)
} tgeo_polygon;

#endif

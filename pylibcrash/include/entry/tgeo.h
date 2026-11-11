typedef struct {
  uint8_t clut_x:4;
  uint8_t clip:1;
  uint8_t semi_trans:2;
  uint8_t type:1;
  uint8_t r;
  uint8_t g;
  uint8_t b;
  eid_t tpage;
  uint32_t offs_y:5;
  uint32_t :1;
  uint32_t clut_y:7;
  uint32_t offs_x:5;
  uint32_t segment:2;
  uint32_t color_mode:2;
  uint32_t region_index:10;
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
  uint16_t a_idx;
  uint16_t b_idx;
  uint16_t c_idx;
  uint16_t texinfo_idx:15;
  uint16_t flag:1;
} tgeo_polygon;

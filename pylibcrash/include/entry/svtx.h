typedef struct {
  int8_t x;
  int8_t y;
  int8_t z;
  int8_t normal_x;
  int8_t normal_y;
  int8_t normal_z;
} svtx_vertex;
typedef struct {
  uint32_t length;
  eid_t tgeo;
  int32_t x;
  int32_t y;
  int32_t z;
  uint32_t bound_x1;
  uint32_t bound_y1;
  uint32_t bound_z1;
  uint32_t bound_x2;
  uint32_t bound_y2;
  uint32_t bound_z2;
  int32_t col_x;
  int32_t col_y;
  int32_t col_z;
  svtx_vertex vertices[];
} svtx_frame;

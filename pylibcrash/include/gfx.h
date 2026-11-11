typedef struct {
uint16_t poly_idx:12; uint16_t world_idx:3; uint16_t flag:1;
} poly_id;
typedef struct {
  int32_t x;
  int32_t y;
  int32_t z;
} vec32;
typedef struct {
  uint32_t x;
  uint32_t y;
  uint32_t z;
} uvec32;
typedef struct {
  int16_t x;
  int16_t y;
  int16_t z;
} vec16;
typedef struct {
  uint16_t x;
  uint16_t y;
  uint16_t z;
} uvec16;
typedef struct {
  float x;
  float y;
  float z;
} fvec;
typedef vec32 pnt32;
typedef vec16 pnt16;
typedef uvec32 upnt32;
typedef uvec16 upnt16;
typedef vec32 ang32;
typedef vec16 ang16;
typedef uvec32 uang32;
typedef uvec16 uang16;
typedef fvec fpnt;
typedef fvec fang;
typedef struct {
  fpnt verts[3];
  fpnt vertuvws[3];
  uint32_t texid;
  uint32_t pad1;
  uint32_t pad2;
} fpoly;
typedef struct {
  fpnt verts[4];
  fpnt vertuvws[4];
  uint32_t texid;
  uint32_t pad1;
  uint32_t pad2;
} fquad;
extern int16_t ang16_sin(int16_t ang);
extern int16_t ang16_cos(int16_t ang);
extern pnt32 mat33_transform(int16_t mat[3][3], pnt32 pnt);
extern void mat33_rotation(int16_t (*mat)[3][3], ang32 rot);
extern void wgeo_project(entry *world, vec32 cam_trans, int16_t ms_cam_rot[3][3], vec32 screen_offset, int normalize, int pcsx, poly_id *poly_ids, fpoly *polys, int *poly_count);
extern void zdat_project(nsf *nsf, entry *zone, int path_idx, int path_pt_idx, vec32 screen_offset, vec32 cam_trans, ang32 cam_rot, int normalize, int pcsx, poly_id *poly_ids, fpoly *polys, int *poly_count);
typedef void (*pshader_t)(poly_id, fpoly, pnt32, uint8_t(*)[4]);
extern void draw_polys_wireframe(poly_id *poly_ids, fpoly *polys, uint32_t poly_count, pshader_t shader, uint32_t w, uint32_t h, uint8_t *pixels);

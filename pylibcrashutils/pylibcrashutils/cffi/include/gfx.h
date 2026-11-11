typedef struct {
  uint16_t poly_idx:12;
  uint16_t world_idx:3;
  uint16_t flag:1;
} poly_id;
typedef struct {
  union { float x; int xi; };
  union { float y; int yi; };
  union { float z; int zi; };
} fvec;
typedef fvec fpnt;
typedef struct {
  fpnt verts[3];
  fpnt vertuvws[3];
  uint32_t texid;
  uint32_t pad1;
  uint32_t pad2;
} fpoly;
extern void compute_visible_polys(poly_id *poly_ids, fpoly *polys, 
                                  int *poly_count, int w, int h, 
                                  float near, int pcsx);
extern uint32_t *get_zbuf_image(uint32_t *buf, int w, int h, int scale, 
                                int pcsx);

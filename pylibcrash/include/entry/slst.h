typedef struct {
  uint16_t split_idx;
  uint16_t swaps_idx;
  uint16_t data[];
} slst_delta;
typedef struct {
  uint16_t length;
  uint16_t type;
  union {
    poly_id poly_ids[0];
    slst_delta delta;
  };
} slst;
typedef struct {
uint16_t idx:11; uint16_t offset:4; uint16_t fmt:1;
} slst_swap_fmta;
typedef struct {
uint16_t offset:12; uint16_t :2; uint16_t fmt_2:2; uint16_t idx:12; uint16_t :2; uint16_t fmt:2;
} slst_swap_fmtb;
typedef struct {
uint16_t offset:5; uint16_t idx:9; uint16_t fmt:2;
} slst_swap_fmtc;
typedef struct {
  int i;
  int start;
  int end;
  uint16_t node;
  poly_id poly;
  int idx;
  int len;
  int count;
} slst_context;
typedef struct {
  void (*on_copy)(int);
  void (*on_add)(slst_context *);
  void (*on_remove)(slst_context *);
  void (*on_swap)(slst_context *);
} slst_callbacks;
extern void slst_decode_forward(entry *slst, int idx,
                                poly_id *src, poly_id *dst,
                                int src_len, int *dst_len,
                                slst_callbacks *callbacks);
extern void slst_decode_backward(entry *slst, int idx,
                                 poly_id *src, poly_id *dst,
                                 int src_len, int *dst_len,
                                 slst_callbacks *callbacks);
extern slst *slst_encode(poly_id *src, poly_id *dst, 
                         int src_len, int dst_len,
		                     size_t *slst_size);
typedef struct {
  int op;
  int src_idx;
  int dst_idx;
} poly_id_delta;

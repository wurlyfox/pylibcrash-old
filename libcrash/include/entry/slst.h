#ifndef SLST_H
#define SLST_H

#include "types.h"
#include "entry.h"

#ifndef S_POLY_ID
#define S_POLY_ID

#define poly_id_val(p) (*(uint16_t*)(&p) & 0x7FFF)
#define poly_ids_eq(a,b) (poly_id_val(a)==poly_id_val(b))

typedef struct {
BITFIELDS_03(
  uint16_t flag:1,
  uint16_t world_idx:3,
  uint16_t poly_idx:12
)
} poly_id;

#endif

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
BITFIELDS_03(
  uint16_t fmt:1,
  uint16_t offset:4,
  uint16_t idx:11
)
} slst_swap_fmta;

typedef struct {
BITFIELDS_06(
  uint16_t fmt:2,
  uint16_t :2,
  uint16_t idx:12,
  uint16_t fmt_2:2,
  uint16_t :2,
  uint16_t offset:12
)
} slst_swap_fmtb;

typedef struct {
BITFIELDS_03(
  uint16_t fmt:2,
  uint16_t idx:9,
  uint16_t offset:5
)
} slst_swap_fmtc;

typedef struct {
  int i;         // iterator position within section
  int start;     // start of the section
  int end;       // end of the section
  uint16_t node; // last node read
  poly_id poly;  // poly id to insert
  int idx;       // next index to insert/skip poly id
  int len;       // num of remaining poly ids to insert/skip
  int count;     // num of poly ids inserted/skipped
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
                                 
#endif

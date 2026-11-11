#ifndef SLST_STATS_H
#define SLST_STATS_H

#include "entry/slst.h"

typedef struct slst_context_desc {
  int type;
  struct slst_context_desc *next; 
  union {
    slst_context context;
    int count_copy;
  };
} slst_context_desc;

typedef struct {
  int stage_count;
  slst_context_desc *desc_heads[1000];
  union {
    slst_context_desc *desc_tails[1000];
    slst_context_desc *descs_sorted_a[1000];
  };
  union {
    int index_map[1000];
    slst_context_desc *descs_sorted_b[1000];
  };
  poly_id interim[1000];
} slst_swap_struct;

typedef struct {
  int src_len;
  int dst_len;
  poly_id *src;
  poly_id *dst;
  int addrem_desc_count;
  int swap_desc_count;
  slst_context_desc addrem_descs[1000];
  slst_context_desc swap_descs[1000];
  slst_swap_struct swap;
} slst_stats_context;


typedef struct {
  int is_head:1;
  int is_tail:1;
  int type:3;
  int i:27;
  poly_id poly_id;
  slst_context_desc *desc;  
} slst_stats_node;

typedef struct {
  int stage_count;
  int node_count;
  slst_stats_node *stages[32];
  slst_stats_node nodes[];
} slst_stats;

extern void slst_stats_summary(entry *slst, int idx, 
                               poly_id *src, poly_id *dst, 
                               int src_len, int *dst_len, 
                               slst_stats *stats);
extern void slst_stats_poly_ids(poly_id *poly_ids, int len, 
                                slst_stats *stats);
extern void slst_stats_addrem_summary(slst_stats_context *stats_context, 
                                      slst_stats *stats);
extern void slst_stats_swap_summary(slst_stats_context *stats_context, 
                                    slst_stats *stats);
extern void slst_stats_swap_id(char *id_str, int id); 

#endif

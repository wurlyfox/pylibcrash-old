/**
 * extensions to the slst decoding functions for text visual 
 * representation of list changes 
 * 
 */ 

#include "misc/slst_stats.h"

static slst_stats_context stats_context;

static void slst_stats_copy(int count_copy) {
  int idx;
  slst_context_desc *desc;
  
  idx = stats_context.addrem_desc_count++;
  desc = &stats_context.addrem_descs[idx];
  
  desc->type = 1; // copy
  desc->count_copy = count_copy;
}

static void slst_stats_add(slst_context *add) {
  int idx;
  slst_context_desc *desc;
  
  idx = stats_context.addrem_desc_count++;
  desc = &stats_context.addrem_descs[idx];

  desc->type = 2; // add        
  memcpy(&desc->context, add, sizeof(slst_context));
}

static void slst_stats_remove(slst_context *rem) {
  int idx;
  slst_context_desc *desc;
  
  idx = stats_context.addrem_desc_count++;
  desc = &stats_context.addrem_descs[idx];

  desc->type = 3; // remove     
  memcpy(&desc->context, rem, sizeof(slst_context));
}

static void slst_stats_swap(slst_context *swap) {
  int idx;
  slst_context_desc *desc;
  
  idx = stats_context.swap_desc_count++;
  desc = &stats_context.swap_descs[idx];

  desc->type = 4; // swap       
  memcpy(&desc->context, swap, sizeof(slst_context));
}

static slst_callbacks callbacks = {
  .on_copy = slst_stats_copy,
  .on_add = slst_stats_add,
  .on_remove = slst_stats_remove,
  .on_swap = slst_stats_swap
};


void slst_stats_string(slst_stats *stats, char *str) {
  int i, ii;
  char buf[100], l[3], r[3];
  slst_stats_node *node, *end;
  
  for (i=0;i<stats->stage_count;i++) {
    sprintf(buf, "stats stage %i\n\n", i);
    strcat(str, buf);
    if (i==stats->stage_count-1)
      end = &nodes[stats->node_count];
    else
      end = stats->stages[i+1];
    for (node=stats->stages[i],ii=0;node!=end;node++,ii++) {
      strcpy(l, "  ");
      strcpy(r, "  ");
      if (node->type == 4) {
        slst_stats_swap_id(buf, node->i);
        l[1] = buf[0]; 
        r[0] = buf[1];
      }
      if (node->is_head) {
        if (node->type == 1) { strcpy(l, "+|"); }
        else if (node->type == 2) { strcpy(l, "-|"); }
        else if (node->type == 3) { strcpy(l, " |"); }
      }
      if (node->is_tail) {
        if (node->type == 1) { strcpy(r, "|+"); }
        else if (node->type == 2) { strcpy(r, "|-"); }
        else if (node->type == 3) { strcpy(r, "| "); }
      }
      sprintf(buf, "%s%04x$s", l, (uint16_t)node->poly_id, r);
      strcat(str, buf);
      if ((ii%16)==15)
        strcat(str, "\n");
    }
    strcat(str, "\n\n");
  }
}

void slst_stats_summary(entry *en_slst, int idx, poly_id *src, poly_id *dst, 
                        int src_len, int *dst_len, /*char *stats*/) {
  // char stats_buf[100000];

  stats_context.addrem_desc_count = 0;
  stats_context.swap_desc_count = 0;
  stats_context.src = src;
  stats_context.dst = dst;
  stats_context.src_len = src_len;
   
  slst_decode_forward(en_slst, idx, src, dst, src_len, dst_len, &callbacks);
  
  stats_context.dst_len = *dst_len;

  /*
  stats[0] = '\0';
  slst_stats_poly_ids(src, src_len, stats_buf);
  strcat(stats, stats_buf);
  slst_stats_addrem_summary(&stats_context, stats_buf);
  strcat(stats, stats_buf);
  slst_stats_swap_summary(&stats_context, stats_buf);
  strcat(stats, stats_buf);
  */
  
  
}
 
void slst_stats_node_init(slst_stats_node *node, int type,
                          poly_id poly_id, int is_head, int is_tail, 
                          slst_context_desc *desc, int i) {
  node->type = type;
  node->poly_id = poly_id;
  node->is_head = is_head;
  node->is_tail = is_tail;
  node->desc = desc;
  node->i = i;                              
}

void slst_stats_poly_ids(poly_id *poly_ids, int len, 
                         slst_stats *stats/ *char *stats */) {
  int isrc;
  // char node_str[10];
  poly_id *src;
  slst_stats_node *node;
  
  src = poly_ids;
  // stats[0] = '\0';
  node = &stats->nodes[node_count]
  stats->stages[stats->stage_count++] = node;
  for (isrc=0;isrc<len;isrc++) {
    // sprintf(node_str, "  %04x  ", *(uint16_t*)(src++));
    // strcat(stats, node_str);
    // if (isrc%16 == 15) { strcat(stats, "\n"); }
    slst_stats_node_init(node++, 0, *(src++), 0, 0, 0, 0);
  }  
  // strcat(stats, "\n");
}

void slst_stats_addrem_summary(slst_stats_context *stats_context, 
                               slst_stats *stats /*char *stats*/) {
  int i, idst, count;
  int adding, removing;
  char node_str[10];
  slst_context_desc *desc;
  poly_id *src, poly_id;
  slst_stats_node *node;
  
  adding = 0;
  removing = 0;
  src = stats_context->src;
  // stats[0] = '\0';
  // strcat(stats, "add/remove stage\n");
  node = &stats->nodes[node_count]
  stats->stages[stats->stage_count++] = node;
  for (i=0,idst=0;i<stats_context->addrem_desc_count;i++) {
    desc = &stats_context->addrem_descs[i];
    
    if (desc->type == 1) { // copy
      if (desc->count_copy == 0) continue;
      poly_id = *(src++);
      if ((adding || removing) && (desc->count_copy == 1)) {
        // sprintf(node_str, " |%04x| ", *(uint16_t*)(src++));
        slst_stats_node_init(node, 3, poly_id, 1, 1, desc, 0);
      }
      else if (desc->count_copy > 0) {
        // sprintf(node_str, "  %04x  ", *(uint16_t*)(src++));
        slst_stats_node_init(node, 0, poly_id, 0, 0, desc, 0);
        i--; // reprocess
      }
      desc->count_copy--;
    }
    else if (desc->type == 2) { // add
      poly_id = desc->context.poly;
      count = ((desc->context.node & 0xF000) >> 12) + 1;
      if (count==1) {
        // sprintf(node_str, "+|%04x|+",*(uint16_t*)&desc->context.poly);
        slst_stats_node_init(node, 1, poly_id, 1, 1, desc, 0);
      }
      else if (desc->context.len==count-1) { // first node in seq
        // sprintf(node_str, "+|%04x  ",*(uint16_t*)&desc->context.poly);
        slst_stats_node_init(node, 1, poly_id, 1, 0, desc, 0);
        adding = 1;
      }
      else if (desc->context.len==0) { // last node in seq
        // sprintf(node_str, "  %04x|+", *(uint16_t*)&desc->context.poly);
        slst_stats_node_init(node, 1, poly_id, 0, 1, desc, 0);
        adding = 0;
      }
      else {
        // sprintf(node_str, "  %04x  ", *(uint16_t*)&desc->context.poly);
        slst_stats_node_init(node, 0, poly_id, 0, 0, desc, 0);
      }
    }
    else if (desc->type == 3) { // remove
      poly_id = *(src++);
      count = ((desc->context.node & 0xF000) >> 12) + 1;
      if (count==1) {
        // sprintf(node_str, "-|%04x|-", *(uint16_t*)(src++));
        slst_stats_node_init(node, 2, poly_id, 1, 1, desc, 0);
      }
      else if (desc->context.len==count-1) { // first node in seq
        // sprintf(node_str, "-|%04x  ", *(uint16_t*)(src++));
        slst_stats_node_init(node, 1, poly_id, 1, 0, desc, 0);
        removing = 1;
      }
      else if (desc->context.len==0) { // last node in seq
        // sprintf(node_str, "  %04x|-", *(uint16_t*)(src++));
        slst_stats_node_init(node, 1, poly_id, 0, 1, desc, 0);
        removing = 0;
      }
      else {
        // sprintf(node_str, "  %04x  ", *(uint16_t*)(src++));
        slst_stats_node_init(node, 0, poly_id, 0, 0, desc, 0);
      }
    }   
        
    // strcat(stats, node_str);
    // if (idst%16 == 15) { strcat(stats, "\n"); }
    idst++;
    node++;
    stats->node_count++;
  }
  // strcat(stats, "\n");
}

void slst_stats_swap_id(char *id_str, int id) {
  int i, pl, len;
  
  for (len=1,pl=id;pl/=62;len++);
  for (i=len-1,pl=id;i>=0;i--) {
    id_str[i] = pl % 62;
    id_str[i] += '0';
    if (id_str[i] > '9')
      id_str[i] += 'A' - '9';
    if (id_str[i] > 'Z')
      id_str[i] += 'a' - 'Z';
    pl /= 62;
  }
  id_str[len] = '\0'; 
}

int sort_swap_descs_a(slst_context_desc *desc_a, 
                      slst_context_desc *desc_b) {
  int a_idx, b_idx;
  a_idx = desc_a->context.idx;
  b_idx = desc_b->context.idx;
  
  if (a_idx > b_idx) return 1;
  if (a_idx < b_idx) return -1;
  return 0;
}

int sort_swap_descs_b(slst_context_desc *desc_a, 
                      slst_context_desc *desc_b) {
  int a_idx, b_idx;
  a_idx = desc_a->context.idx+desc_a->context.len+1;
  b_idx = desc_b->context.idx+desc_b->context.len+1;
  
  if (a_idx > b_idx) return 1;
  if (a_idx < b_idx) return -1;
  return 0;
}

/**
 * 
 * summary stats for swaps are a bit trickier than for copies/adds/rems
 * 
 * firstly, since we dont save the intermediary list (between rebuild 
 * and swap) in either the forward or backward case, we have to 
 * reconstruct it:
 * 
 * - for forward, since swapping comes second, we (un)swap the dst list
 *   to get the intermediary list
 * - for backward, since swapping comes first, we swap the src list to
 *   get the intermediary list
 * 
 * the swap stats show the changes from
 * - intermediary list to dst list for forward
 * - src list to intermediary list for backward
 * 
 * the swap stats are shown in multiple stages, such that
 * - no 2 swaps in the same stage are 'overlapping' (have a common idx)
 * - the first stage represents operating on the intermediary list for 
 *   forward and src list for backward
 * - any other stage represents operating on the results of the previous 
 *   stage
 * - the results of the last stage is the dst list for forward and 
 *   intermediary list for backward
 *
 * to get the swaps in each stage, we run through each swap in order: if
 * a swap does not overlap a swap so far added to any existing stage, then
 * we add it to stage 1, else if it overlaps a swap in stage n and n is
 * maximum then we add it to stage n+1. 
 * 
 * for example:   
 *  1 6 9 B 2 7 A 3 8 4 5
 * 1 2 3 4 5 6 7 8 9 A B C  
 *
 * (where the order of the swap of 2 numbers/letters in the below list is
 *  indicated by the order of the id number/letter between them in the 
 *  above list)
 * 
 * stage 1 would be 1, 2, 3, 4
 * stage 2 would be 5, 6, 7, 8
 * stage 3 would be 9, A
 * stage 4 would be B
 * 
 * then we can show the transformation of the list in individual stages:
 * 
 * 1 2 3 4 5 6 7 8 9 A B C
 * <=>     <=>   <=> <=>
 * 2 1 3 4 6 5 7 9 8 B A C
 *   <=>     <=>   <=> <=>
 * 2 3 1 4 5 7 5 9 B 8 C A
 *     <=>     <=> 
 * 2 3 4 1 5 7 9 5 B 8 C A
 *       <=>
 * 2 3 4 5 1 7 9 5 B 8 C A
 * 
 * notice that, in the forward case, if all we know are the swap indices
 * and we only have the dst list, we can apply the stages in reverse to
 * get the stage stats all the way back to the intermediary list
 */
void slst_stats_swap_summary(slst_stats_context *stats_context, 
                             slst_stats *stats /* char *stats */) {
  int i, ii, idst;
  int a_idx, b_idx;
  int stage_max, stage_len;
  // char node_str[10], id_str[3];
  // char l_stats[100000];
  poly_id *dst, *interim, tmp, poly_id;
  slst_swap_struct *swap;
  slst_context_desc *desc, *desc_a, *desc_b;
  int desc_a_idx, desc_b_idx;
  slst_stats_node *node;
  
  swap = &stats_context->swap;
  dst = stats_context->dst;
  interim = swap->interim;
  memcpy(interim, dst, stats_context->dst_len*sizeof(poly_id));
    
  stage_max = 0;
  swap->stage_count = 0;
  // stats[0] = '\0';
  for (i=0;i<stats_context->swap_desc_count;i++) {
    desc = &stats_context->swap_descs[i];
    
    a_idx = desc->context.idx;
    b_idx = desc->context.idx+desc->context.len+1;
  
    stage_max = max(swap->index_map[a_idx],
                    swap->index_map[b_idx]);
    swap->index_map[a_idx]++;
    swap->index_map[b_idx]++;
    if (stage_max >= swap->stage_count) {
      swap->desc_heads[stage_max] = desc;
      swap->desc_tails[stage_max] = desc;
      swap->stage_count++;
    }
    else {
      swap->desc_tails[stage_max]->next = desc;
      swap->desc_tails[stage_max] = desc;
    }
  }
   
  stats->stage_count += swap->stage_count;
  for (i=swap->stage_count-1;i>=0;i--) {
    // l_stats[0] = '\0';
    node = stats->stages[i+1];
    for (desc=swap->desc_heads[i],ii=0;desc;ii++) {
      swap->descs_sorted_a[ii] = desc;
      swap->descs_sorted_b[ii] = desc;
      desc = desc->next;
    }
    stage_len = ii;
    if (stage_len > 1) {
      // sort the swap operations, which are non-overlapping
      qsort(swap->descs_sorted_a, ii,
            sizeof(slst_context_desc*), sort_swap_descs_a);
      qsort(swap->descs_sorted_b, ii,
            sizeof(slst_context_desc*), sort_swap_descs_b);
    }
    desc_a_idx = 0;
    desc_b_idx = 0;
    dst = interim;
    for (idst=0;idst<stats_context->dst_len;idst++) {
      poly_id = *(dst++);
      a_idx = -1, b_idx = -1;
      if (desc_a_idx < stage_len) {
        desc_a = swap->descs_sorted_a[desc_a_idx];
        a_idx = desc_a->context.idx;
      }
      if (desc_b_idx < stage_len) {
        desc_b = swap->descs_sorted_b[desc_b_idx];
        b_idx = desc_b->context.idx+desc_b->context.len+1;
      }
      if (idst == a_idx) {
        // slst_stats_swap_id(&id_str, (int)desc_a->context.i);  
        // sprintf(node_str, "%c|%04x|%c", 
        //        id_str[0], *(uint16_t*)(dst++), id_str[1]);
        slst_stats_node_init(node,4,poly_id,1,1,desc_a,desc_a->context.i);
        desc_a_idx++;
      }
      else if (idst == b_idx) {
        // slst_stats_swap_id(&id_str, (int)desc_b->context.i);
        // sprintf(node_str, "%c|%04x|%c", 
        //        id_str[0], *(uint16_t*)(dst++), id_str[1]);
        slst_stats_node_init(node,4,poly_id,1,1,desc_b,desc_b->context.i);
        // do the swap here
        a_idx = desc_b->context.idx;
        tmp = interim[a_idx];
        interim[a_idx] = interim[b_idx];
        interim[b_idx] = tmp;
        desc_b_idx++;
      }
      else {
        // sprintf(node_str, "  %04x  ", *(uint16_t*)(dst++));
        slst_stats_node_init(node,4,poly_id,1,1,0,0);
      }
      
      // strcat(l_stats, node_str);
      // if (idst%16 == 15) { strcat(l_stats, "\n"); }
    }
    // strcat(l_stats, "\n");
    // strcat(l_stats, stats);
    // sprintf(stats, "swap stage %i\n%s", i, l_stats);
  }
}

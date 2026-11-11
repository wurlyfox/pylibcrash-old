#include "entry/slst.h"

#define min(a,b) ((a)<(b)?a:b)
#define min_3(a,b,c) min(min(a,b),c)

/**
 * annotations for the conditional checks are 
 *  If 
 * - the source point has not reached the end of the source list 
 *   (there are still polygon ids to potentially copy or remove)
 * - there are polygon ids to skip/remove from the source list 
 *   (as specified by the current removing node)
 * - the source point is at (has reached) the index described by the 
 *   current removing node
 *
 * If 
 * - there are polygon ids to add to the destination list (as 
 *   specified by the current adding node)
 * - the source point is at (has reached) the index described by 
 *   the current adding node...
 *   ...or the 'rem.count'th node in advance if a removal is 
 *   currently in progress
 *
 * if
 * - the source point is at neither the index described by the current 
 *   adding node nor the index described by the current removing 
 *   node (so as to have brought control to either of the preceding 
 *   blocks)
 * - the source point has not reached the end of the source list 
 *   (there are still polygon ids to potentially copy or remove)
 *  
 * annotations for min statement are
 * find nearest distance-that between the source point and:
 * - the index specified by current adding node
 * - the index specified by current removing node, or
 * - the end of the source list
 *
 * register mapping
 * delta->swap_idx - fp
 * src_len - gp
 * 
 * add.node  - at?
 * rem.node  - at?
 * add.idx   - t0
 * rem.idx   - t1
 * add.len   - t2
 * rem.len   - t3
 * add.count - t4?
 * rem.count - t5
 * 
 * add.i     - t7
 * rem.i     - s0
 * add.start - sp
 * rem.start - s0
 * 
 * idst      - v0
 * isrc      - v1
 * 
 * // nodes = (uint16_t*)slst + 2
 * // rem.start = 2
 *
 * // &nodes[rem.start] = (uint16_t*)slst + 4
 * // &nodes[add.start] = (uint16_t*)slst + 2 + slst->delta.split_idx
 * // &nodes[swap.start] = (uint16_t*)slst + 2 + slst->delta.swaps_idx
 * // &nodes[swap.end] = (uint16_t*)slst + 2 + slst->length
 */

static const int _n1 = -1;
static inline void slst_rem_next(slst_context *rem, uint16_t *nodes) {
  if (rem->len > 0) {
    rem->poly = *(poly_id*)&nodes[rem->i++];
    rem->idx += rem->poly.flag; // advances by 1 if set
  }
  else { // all rem.len ids specified by the node have been removed
    rem->node = nodes[rem->i++]; // process the next removing node (at)
    if (rem->i < rem->end && rem->node != 0xFFFF) {
      rem->idx = rem->node & 0xFFF;                
      rem->len = ((rem->node & 0xF000) >> 12) + 1; // min 1
    }    
    else {
      rem->idx = 0xFFFF00; // null index
      rem->len = 0;        // no removal
    }
       
    if (rem->len > 0) // preparative step
      rem->poly = *(poly_id*)&nodes[rem->i++]; 
    else                 // ==> only applicable to the first slst_rem_next
      rem->poly = *(poly_id*)&_n1; // ==> call?; optimized out otherwise?
  }
}

static inline void slst_add_next(slst_context *add, uint16_t *nodes) {
  if (add->len > 0) {
    add->poly = *(poly_id*)&nodes[add->i++]; // grab next polygon id in seq
    add->idx += add->poly.flag;  // advances by 1
  }                                   
  else { // process the next adding node
    add->node = nodes[add->i++];
    if (add->i < add->end && add->node != 0xFFFF) {
      add->idx = add->node & 0xFFF;                
      add->len = ((add->node & 0xF000) >> 12) + 1;  // min 1
    }
    else { 
      add->idx = 0xFFFF00;
      add->len = 0;
    }
      
    if (add->len > 0)
      add->poly = *(poly_id*)&nodes[add->i++]; 
  }
}
    
void slst_decode_forward(entry *en_slst, int idx, poly_id *src, poly_id *dst, 
                         int src_len, int *dst_len,
                         slst_callbacks *callbacks) {
  slst *slst;
  uint16_t *nodes;
  slst_context add, rem, swap;
  int isrc, idst, i, count_copy;
  int node_len;
  poly_id tmp;
  
  slst = en_slst->items[idx];
  nodes = (uint16_t*)&slst->delta;
  
  rem.start = offsetof(slst_delta, data)/sizeof(slst->delta.data[0]);
  add.start = rem.end = slst->delta.split_idx;
  swap.start = add.end = slst->delta.swaps_idx; 
  swap.end = slst->length;
   
  rem.i = rem.start;
  add.i = add.start;
  
  rem.len = 0; // done so the initial calls to add/rem_next 
  add.len = 0; // run only the else block
  
  slst_rem_next(&rem, nodes);
  slst_add_next(&add, nodes);
  
  isrc = 0;
  idst = 0;
  add.count = 0;
  rem.count = 0;

  do {
    if (isrc < src_len &&
           0 < rem.len &&
        ((rem.idx-1)-isrc) == 0) {
      isrc++; // advance the source point (this is the 'removal')
      
      rem.len--;
      rem.count++; // skips/removes only one id at a time
      
      if (callbacks && callbacks->on_remove)
        (*callbacks->on_remove)(&rem);
      slst_rem_next(&rem, nodes);
    } 
    else if (add.len > 0 &&
             ((add.idx + rem.count) - isrc) == 0) {
      add.poly.flag = 0;
      dst[idst++] = add.poly; // append the next poly id at insertion pt
      
      add.len--;
      add.count++; // unused
      
      if (callbacks && callbacks->on_add)
        (*callbacks->on_add)(&add);
      slst_add_next(&add, nodes);      
    }
    else if (isrc < src_len) {
      count_copy = min_3((add.idx + rem.count) - isrc,
                         rem.idx - (isrc+1), 
                         src_len - (isrc+1));
      if (count_copy == 0) { count_copy = 1; }

      if (callbacks && callbacks->on_copy)
        (*callbacks->on_copy)(count_copy);
      for (i=0;i<count_copy;i++) {
        dst[idst++] = src[isrc++];
      }
    }
  } while (isrc < src_len ||
           add.len > 0 ||
           rem.len > 0);
  *dst_len = idst;

  swap.i = swap.start;
  
  while (swap.i < swap.end) {
    swap.node = nodes[swap.i];
    if (swap.node == 0xFFFF) { break; } 
    
    if (swap.node & 0x8000) { // fmt A: 1BBBBAAA AAAAAAAA
      swap.idx = ((slst_swap_fmta*)&nodes[swap.i])->idx;
      swap.len = ((slst_swap_fmta*)&nodes[swap.i])->offset;
      node_len = sizeof(slst_swap_fmta)/sizeof(uint16_t);
    } // fmt C
    else if ((swap.node & 0xC000) == 0x4000) { // is the follow-up node of the preceding node
      swap.idx += ((slst_swap_fmtc*)&nodes[swap.i])->idx;
      swap.len = ((slst_swap_fmtc*)&nodes[swap.i])->offset + 16;
      node_len = sizeof(slst_swap_fmtc)/sizeof(uint16_t);
    }
    else { // fmt B: 0000AAAA AAAAAAAA 0000BBBB BBBBBBBB     
      swap.idx = ((slst_swap_fmtb*)&nodes[swap.i])->idx;
      swap.len = ((slst_swap_fmtb*)&nodes[swap.i])->offset;
      node_len = sizeof(slst_swap_fmtb)/sizeof(uint16_t);
    }

    if (callbacks && callbacks->on_swap)
      (*callbacks->on_swap)(&swap);
    tmp = dst[swap.idx];
    dst[swap.idx] = dst[swap.idx+swap.len+1];
    dst[swap.idx+swap.len+1] = tmp;
    
    swap.i += node_len;
  }
}

void slst_decode_backward(entry *en_slst, int idx, poly_id *src, poly_id *dst, 
                          int src_len, int *dst_len,
                          slst_callbacks *callbacks) {
  slst *slst;
  uint16_t *nodes;
  slst_context add, rem, swap;
  int isrc, idst, i, count_copy;
  poly_id tmp;
  
  slst = en_slst->items[idx];
  nodes = (uint16_t*)&slst->delta;
  add.start = offsetof(slst_delta, data)/sizeof(slst->delta.data[0]);
  rem.start = add.end = slst->delta.split_idx;
  swap.start = rem.end = slst->delta.swaps_idx; 
  swap.end = slst->length;

  swap.i = swap.end-1;
  
  while (swap.i >= swap.start) {
    swap.node = nodes[swap.i];
    if (swap.node == 0xFFFF) { 
      swap.i--;
      continue;
    }
    if (swap.node & 0x8000) { // fmt A: 1BBBBAAA AAAAAAAA
      swap.i -= sizeof(slst_swap_fmta)/sizeof(uint16_t)-1;
      swap.idx = ((slst_swap_fmta*)&nodes[swap.i])->idx;
      swap.len = ((slst_swap_fmta*)&nodes[swap.i])->offset;
    } // fmt C
    else if ((swap.node & 0xC000) == 0x4000) {
      swap.i -= sizeof(slst_swap_fmtc)/sizeof(uint16_t)-1;
      swap.idx = ((slst_swap_fmtc*)&nodes[swap.i])->idx;
      swap.len = ((slst_swap_fmtc*)&nodes[swap.i])->offset + 16;
      if (nodes[swap.i-1] & 0x8000) // lookback a short
        swap.idx += ((slst_swap_fmta*)&nodes[swap.i]-1)->idx;
      else
        swap.idx += ((slst_swap_fmtb*)&nodes[swap.i]-1)->idx;
    }
    else { // fmt B: 0000AAAA AAAAAAAA 0000BBBB BBBBBBBB     
      swap.i -= sizeof(slst_swap_fmtb)/sizeof(uint16_t)-1;
      swap.idx = ((slst_swap_fmtb*)&nodes[swap.i])->idx;
      swap.len = ((slst_swap_fmtb*)&nodes[swap.i])->offset;
    }

    if (callbacks && callbacks->on_swap)
      (*callbacks->on_swap)(&swap);
    tmp = dst[swap.idx];
    dst[swap.idx] = dst[swap.idx+swap.len+1];
    dst[swap.idx+swap.len+1] = tmp;
    
    swap.i--; // go back a short; we don't know the specific struct yet
  }
  
  rem.i = rem.start;
  add.i = add.start;
  
  rem.len = 0; // done so the initial calls to add/rem_next 
  add.len = 0; // run only the else block
  
  slst_rem_next(&rem, nodes);
  slst_add_next(&add, nodes);
  
  isrc = 0;
  idst = 0;
  add.count = 0;
  rem.count = 0;

  do {
    if (isrc < src_len &&
           0 < rem.len &&
        ((rem.idx+rem.count)-isrc) == 0) {
      isrc++; // advance the source point (this is the 'removal')
      
      rem.len--;
      rem.count++; // skips/removes only one id at a time

      if (callbacks && callbacks->on_remove)
        (*callbacks->on_remove)(&rem);      
      slst_rem_next(&rem, nodes);
    } 
    else if (add.len > 0 &&
             (((add.idx + rem.count) - (add.count+1)) - isrc) == 0) {
      add.poly.flag = 0;
      dst[idst++] = add.poly; // append the next poly id at insertion pt
      
      add.len--;
      add.count++;
      
      if (callbacks && callbacks->on_add)
        (*callbacks->on_add)(&add);
      slst_add_next(&add, nodes);      
    }
    else if (isrc < src_len) {
      count_copy = min_3((add.idx + (rem.count-add.count)) - (isrc+1),
                         (rem.idx + rem.count) - isrc, 
                         src_len - (isrc+1));
      if (count_copy == 0) { count_copy = 1; }

      if (callbacks && callbacks->on_copy)
        (*callbacks->on_copy)(count_copy);
      for (i=0;i<count_copy;i++) {
        dst[idst++] = src[isrc++];
      }
    }
  } while (isrc < src_len ||
           add.len > 0 ||
           rem.len > 0);
  *dst_len = idst;
}

typedef struct {
  poly_id *src;
  poly_id *dst;
  int src_len;
  int dst_len;
  poly_id_delta delta_map[0x8000];
  poly_id_delta *deltas[0x800];
  int delta_count;
  poly_id_delta swaps[0x800];
  int swap_count;
} slst_encode_context;

#define poly_id_dst_idx(a) \
  context->delta_map[poly_id_val(interim[a])].dst_idx
#define poly_id_swap_cmp(a,b) \
  (poly_id_dst_idx(a) > poly_id_dst_idx(b))
#define poly_id_swap(a,b) { \
  tmp = interim[a]; \ 
  interim[a] = interim[b]; \
  interim[b] = tmp; \
  delta = &context->swaps[context->swap_count++]; \
  context->deltas[context->delta_count++] = delta; \
  delta->op = 4; \
  delta->src_idx = a; \
  delta->dst_idx = b; \
} 

/**
 * initializes the delta map for an slst encoding context
 * 
 * calculates the set intersection and differences between the 
 * src and dst lists. maps each poly id (in each list) to a delta with
 * the index of the poly id in the src and/or dst list(s) and an op 
 * depending on which lists it belongs to:
 *   -1 - remove (exists only in the src list)
 *    1 - add (exists only in the dst list)
 *    0 - copy (exists in both lists)
 * */
static inline void slst_encode_init_map(slst_encode_context *context) {
  int i;
  poly_id poly_id;
  poly_id_delta *delta;
  
  memset(context->delta_map, 0, sizeof(context->delta_map));
  for (i=0;i<context->src_len;i++) {
    poly_id = context->src[i];
    delta = &context->delta_map[poly_id_val(poly_id)];
    delta->op = -1;
    delta->src_idx = i;
  }
  for (i=0;i<context->dst_len;i++) {
    poly_id = context->dst[i];
    delta = &context->delta_map[poly_id_val(poly_id)];
    delta->op += 1;
    delta->dst_idx = i;
  }
}

/**
 * marks copies in the delta map for an slst encoding context as no-swap
 * 
 * copy deltas marked as no-swap indicate that the correspondng poly id 
 * need not be swapped after copying from src list to acheive the same 
 * ordering as in the dst list. 
 * 
 * no-swap copy deltas have op = 2 instead of 0, where 0 indicates a 
 * [swap] copy
 * 
 * poly ids with no-swap deltas are exactly those in the longest common 
 * subsequence between src and dst
 */
static inline void slst_encode_mark_copies(slst_encode_context *context) {
  int i,j,k;
  poly_id copied_src[0x1000];
  poly_id copied_dst[0x1000];
  int copy_count;
  poly_id lcs[0x8000]; int lcs_count;
 // int *c_table, c_table_len;
  poly_id poly_id, src_id, dst_id;
  poly_id_delta *delta;
  int c_table[0x40000];
  
  // get copies (only copied poly ids will be in lcs)
  copy_count = 0;
  for (i=0;i<context->src_len;i++) {
    poly_id = context->src[i];
    delta = &context->delta_map[poly_id_val(poly_id)];
    if (delta->op) continue;
    copied_src[copy_count++] = poly_id;
  }
  copy_count = 0;
  for (i=0;i<context->dst_len;i++) {
    poly_id = context->dst[i];
    delta = &context->delta_map[poly_id_val(poly_id)];
    if (delta->op) continue;
    copied_dst[copy_count++] = poly_id;
  }

  // get lcs between src and dst 
  #define c_tab(i,j) c_table[(i)+((j)*(copy_count+1))]
  // c_table_len = copy_count*(copy_count+2)+1;
  // c_table = (int*)malloc(c_table_len*sizeof(int));
  for (i=0;i<copy_count;i++) {
    c_tab(i,0) = 0;
    c_tab(0,i) = 0;
  }
  for (i=1;i<=copy_count;i++) {
    for (j=1;j<=copy_count;j++) {
      src_id = copied_src[i-1];
      dst_id = copied_dst[j-1];
      if (poly_ids_eq(src_id, dst_id))
        c_tab(i,j) = c_tab(i-1,j-1) + 1;
      else
        c_tab(i,j) = max(c_tab(i,j-1),c_tab(i-1,j));
    }
  }
  lcs_count = c_tab(--i,--j);
  
  k = lcs_count-1; 
  while (i != 0 && j != 0) {
    src_id = copied_src[i-1];
    dst_id = copied_dst[j-1];
    if (poly_ids_eq(src_id, dst_id)) {
      lcs[k--] = src_id;
      i--; j--;
    }
    else if (c_tab(i,j-1) > c_tab(i-1,j)) j--;
    else i--;
  }

  // mark all ids in the lcs as no-swap
  for (i=0;i<lcs_count;i++) {
    poly_id = lcs[i];
    delta = &context->delta_map[poly_id_val(poly_id)];
    delta->op = 2; // copy
  }
  
  // free(c_table);
}

typedef struct {
  int src_len;
  int dst_len;
  int src_idx;
  int dst_idx;
  int processed;
} slst_partition;

typedef struct {
  int part_top;
  slst_partition part_stack[0x1000];
  int swap_top;
  poly_id swap_stack[0x1000];
} slst_swap_context;

// only length(s) of src partition will change when splitting
// a new partition is created for the second half of the split
#define slst_encode_split_part(c,p,si,di,sl,dl,rsi,rdi) \
  p->src_len = rsi; \
  p->dst_len = rdi; \
  p->processed = 0; \
  p = &c->part_stack[c->part_top++]; \
  p->src_idx = si; \
  p->dst_idx = di; \
  p->src_len = sl - rsi; \
  p->dst_len = dl - rdi; \
  p->processed = 0; 

/**
 * recursively finds a sequence of poly ids (continuing the current)
 * that can be swapped in place in the interim list without changing 
 * the positions of ids whose presences would be required to maintain 
 * the alignment of other ids in the longest common subsequence between 
 * src and dst
 * 
 * for example the 2 sequences ABCDEFHIKLJ are aligned ABCDEFHIKLJ
 *                             ACKIHJLBDEM             A CKI HJ LBDEM
 * 
 * for the lcs ACHL, one may try swapping the pairs (E,I),(E,J),(E,B) 
 * [in order]. however, E in its position after the swaps would need to
 * be removed to maintain the alignment of the lcs ids, and this is not
 * possible because swapping can only occur post add/remove. furthermore
 * E could not be used for such a swap at such position because it must
 * be removed as a src id in any configuration which does not align it,
 * as a dst id, with the J src id.
 * 
 * on the other hand if the J src id is chosen to align with the E dst 
 * id then there is a cycle of swaps (E,I)->(I,J)->(J,E) which does not
 * interfere with any add/removes. however, choosing this may have 
 * prevented discovering a longer swap cycle starting with J,D (as D,B,
 * and M are forcibly removed from the src list in this configuration)
 * 
 * the search is lazy as it returns the first swap cycles found, however 
 * it only considers when a full cycle is made (i.e. one that cycles back 
 * to the beginning of the sequence, and nowhere else; a shorter cycle
 * -may- be discovered within the traversal, but it is ignored). about
 * N% of [ids which would otherwise have add/remove op delta pairs], on
 * average, are found to be encodable as swaps
 */
static inline int slst_encode_find_swaps(slst_encode_context *context,
                                         slst_swap_context *swap_context, 
                                         poly_id _poly_id) {
  int i,ii;
  poly_id *src, *dst;
  poly_id_delta *delta_map, *delta;
  int src_idx, dst_idx;
  int rel_src_idx, rel_dst_idx;
  int gap_len; 
  int part_idx;
  slst_partition *part, cur;
  poly_id *swap_stack, swap_id;
  int *swap_top;
  int idx,len,op_fst;
  int a_idx, b_idx;
  poly_id tmp;
  
  src = context->src;
  dst = context->dst;
  delta_map = context->delta_map;
  swap_stack = swap_context->swap_stack;
  swap_top = &swap_context->swap_top;

  // skip src ids that will be removed
  if (delta_map[poly_id_val(_poly_id)].op == -1) 
    return 0;
    
  // get index of id in src
  src_idx = delta_map[poly_id_val(_poly_id)].src_idx;
  
  // find the containing partition
  for (part_idx=0;part_idx<swap_context->part_top;part_idx++) {
    part = &swap_context->part_stack[part_idx];
    if (part->src_idx != -1) {
      rel_src_idx = src_idx - part->src_idx;
      if (rel_src_idx >= 0 && rel_src_idx < part->src_len)
        break;
    }
    part = 0;
  }
  if (!part) return 0; // fail if none found
  if (part->dst_idx == -1) return 0; // or if there is no dst part
  cur = *part;

  // get the range of indices of dst ids which can align with
  // the src id to form a place for swapping
  rel_src_idx = src_idx - cur.src_idx;
  gap_len = cur.dst_len - cur.src_len;
  idx = 0;
  len = 0;
  if (gap_len < 0) {
    if (rel_src_idx < cur.dst_len-1)
      len = rel_src_idx;
    else if (rel_src_idx > -gap_len) {
      len = cur.src_len - rel_src_idx;
      idx = cur.dst_len - len;
    }
    else
      len = cur.dst_len;
  }
  else if (gap_len > 0) {
    idx = rel_src_idx;
    len = gap_len+1;
  }
  else {
    idx = rel_src_idx;
    len = 1;
  }

  // skip the first dst id if it is direct copy or swap copy
  op_fst = delta_map[poly_id_val(dst[cur.dst_idx+idx])].op;
  if (op_fst == 0 || op_fst == 2) {
    idx++;
    len--;
  }
        
  // test each dst id
  tmp = _poly_id;
  for (i=idx;i<idx+len;i++) {
    rel_dst_idx = i;
    dst_idx = cur.dst_idx + rel_dst_idx;	
    _poly_id = dst[dst_idx];
    
    // skip added ids as they don't exist in src and cant form a cycle 
    if (delta_map[poly_id_val(_poly_id)].op == 1) continue;
    
    // if the id completes the full cycle of swaps
    if (poly_ids_eq(_poly_id, swap_stack[0])) {     
      // redefines a delta for swap_stack item as swap copy
      // and grabs its dst_idx
      #define get_swap_idx(var,si) \
      swap_id = swap_stack[si]; \
      delta = &delta_map[poly_id_val(swap_id)]; \
      delta->op = 0; \
      var = delta->dst_idx;
      
      // redefine the first swap stack item delta as swap copy
      // and use its dst_idx as 'b index' for all swaps in the cycle
      get_swap_idx(b_idx, 0);
      for (ii=(*swap_top)-1;ii>0;ii--) {
        // redefine the other swap stack item delta as swap copy
        // and use its dst_idx as the 'a index' for a new swap delta      
        get_swap_idx(a_idx, ii);
        // then insert the new swap delta
        delta = &context->swaps[context->swap_count++];
        delta->op = 4;
        delta->src_idx = a_idx;
        delta->dst_idx = b_idx;
      }
          
      // reset the swap stack
      *swap_top = 0;
      slst_encode_split_part(swap_context, part, src_idx, dst_idx,
                             cur.src_len, cur.dst_len,
                             rel_src_idx, rel_dst_idx);
      return 1; // return success
    }
  
    // if the poly id is any other id (already) in the swap sequence,
    // then we've found a cycle that does not begin at the first id;
    // this cycle is shorter than the sequence and any potential longer
    // cycle we might find, so we skip it
    // if no other id past the first one in the shorter cycle is found
    // to complete the current sequence cycle, the shorter cycle may 
    // still be found in future iterations, so nothing is lost by 
    // skipping
    for (ii=0;ii<*swap_top;ii++) {
      if (poly_ids_eq(_poly_id, swap_stack[ii])) 
        break;
    }
    if (ii!=(*swap_top)) continue; // or return/break here?
      
    // otherwise add to the swap stack and recurse, splitting partition
    // to preserve the alignment chosen 
    swap_stack[(*swap_top)++] = _poly_id;
    slst_encode_split_part(swap_context, part, src_idx, dst_idx,
                           cur.src_len, cur.dst_len,
                           rel_src_idx, rel_dst_idx);
    if (slst_encode_find_swaps(context, swap_context, _poly_id))
      return 1;
    else {
      // no swaps were found, so we have to recombine the partition
      //
      // splitting replaced the current part with the left half
      // and allocated/created a new part for the right half
      // due to the order of calls, the right half will always be the 
      // part at the top of the part stack
      // so we simply pop the part stack and restore the original
      // values for the parent of the parts to the left part 
      swap_context->part_top--;      
      (*swap_top)--;
      *part = cur;
    }            
  }
 
  // no cycles were found, so return fail 
  return 0;
}

#define slst_encode_src_part(si,sl) \
  part = &swap_context.part_stack[swap_context.part_top++]; \
  part->src_idx = (si); \
  part->src_len = (sl); \
  part->dst_idx = -1; \
  part->dst_len = 0; \
  part->processed = 0;
  
#define slst_encode_dst_part(pi,di,dl) \
  cond = (pi < swap_context.part_top); \
  idx = cond ? pi++ : swap_context.part_top++; \
  part = &swap_context.part_stack[idx]; \
  part->dst_idx = di; \
  part->dst_len = dl; \
  part->src_idx = cond ? part->src_idx : -1; \
  part->src_len = cond ? part->src_len : 0; \
  part->processed = 0; 
  
/**
 * the non-recursive counterpart to slst_encode_find_swaps
 * 
 * initializes a swap context for the recursive function by partitioning
 * src and dst lists at direct copy ids and then attempts to find swap
 * cycles starting at each src id 
 * (one call to slst_encode_find_swaps per src id)
 * 
 * partitions are split when a swap cycle is discovered; iteration
 * continues until there are no more partitions to split
 */
static inline void slst_encode_mark_swaps(slst_encode_context *context) {
  int i;
  int src_len, dst_len;
  poly_id *src, *dst;
  poly_id_delta *delta_map, *delta;
  slst_swap_context swap_context;
  int part_idx, part_len;
  slst_partition *part, cur;
  int swap_len, src_op;
  int idx, cond;
  
  src_len = context->src_len;
  dst_len = context->dst_len;
  src = context->src;
  dst = context->dst;
  delta_map = context->delta_map;

  context->swap_count = 0;
  // initially assume all swap copies are move operations (replace w op 3)
  for (i=0;i<src_len;i++) {
    delta = &delta_map[poly_id_val(src[i])];
    if (delta->op == 0) delta->op = 3;
  }
  for (i=0;i<dst_len;i++) {
    delta = &delta_map[poly_id_val(dst[i])];
    if (delta->op == 0) delta->op = 3;
  }

  // initialize partitions
  swap_context.part_top = 0;
  swap_context.swap_top = 0;
 
  // divide src and dst into partitions
  part_len = 0;
  for (i=0;i<src_len;i++) {
	part_len++;
    delta = &delta_map[poly_id_val(src[i])];
    if (delta->op == 2) {
	  slst_encode_src_part(i+1-part_len, part_len-1);
	  part_len = 0;
    }
  }
  slst_encode_src_part(src_len-part_len, part_len);
  
  part_len = 0;
  part_idx = 0;
  for (i=0;i<dst_len;i++) {
    part_len++;
    delta = &delta_map[poly_id_val(dst[i])];
    if (delta->op == 2) {
      slst_encode_dst_part(part_idx, i+1-part_len, part_len-1);
      part_len = 0;
    }
  }
  slst_encode_dst_part(part_idx, dst_len-part_len, part_len);

  while (1) {
    // get the next unprocessed partition
    for (i=0;i<swap_context.part_top;i++) {
      part = &swap_context.part_stack[i];
      if (!part->processed) break;
      part = 0;
    }
    if (!part) break;
    
    swap_len = min(part->src_len, part->dst_len) - 1;
    if (swap_len > 0) {
      for (i=part->src_idx;i<part->src_idx+part->src_len;i++) {
        src_op = delta_map[poly_id_val(src[i])].op;
        if (src_op == 0 || src_op == 2)
          continue;
        swap_context.swap_stack[swap_context.swap_top++] = src[i];
        // restart if we found a swap cycle, for the partition has
        // been split and the src iterator is now invalid
        if (slst_encode_find_swaps(context, &swap_context, src[i]))
          break;
        swap_context.swap_top--;
      }
    }
    part->processed = 1;
  }
}

static inline void slst_encode_get_deltas(slst_encode_context *context) {
  int i,j;
  poly_id_delta *delta;
  int src_len, dst_len;
  poly_id *src, *dst;
  poly_id_delta *delta_map;
  poly_id poly_id;
  int src_op, dst_op;
  int tmp;
  
  src_len = context->src_len;
  dst_len = context->dst_len;
  src = context->src;
  dst = context->dst;
  delta_map = context->delta_map;
  
  // get copy/add/remove deltas in order of application
  tmp = 0;
  context->delta_count = 0;
  for (i=0,j=0;i<src_len||j<dst_len;) {
    src_op = i < src_len ? delta_map[poly_id_val(src[i])].op : -2;
    dst_op = j < dst_len ? delta_map[poly_id_val(dst[j])].op : -2;

    if (src_op == dst_op && (src_op == 2 || src_op == 0))
      poly_id = src[j++,i++];
    else if (src_op == -1 || src_op == 3 || j >= dst_len)
      poly_id = src[i++];
    else if (dst_op == 1 || dst_op == 3 || i >= src_len)
      poly_id = dst[j++];

    delta = &delta_map[poly_id_val(poly_id)];
    // quick redef of delta for easy distinguish between move add/remove
    if (src_op == 3) {
	  context->swaps[context->swap_count+tmp] = *delta;
	  delta = &context->swaps[context->swap_count+tmp++];
	  delta->op = -3;
	}
    context->deltas[context->delta_count++] = delta;
  }
  
  // then append swap deltas
  for (i=0;i<context->swap_count;i++) {
    context->deltas[context->delta_count++] = &context->swaps[i];
  }
}

// code left here in case this technique proves to be more optimal in
// certain cases.
//
// originally all non-lcs items were quicksorted after building the
// 'interim list', done by evaluating the delta ops constructed from the
// lcs direct copies and add/removes in order, on the src list (with adds
// sourced from the dst list), to get the swap deltas
// this does not work when the lcs ids are mis-aligned, however

/*
static inline void slst_encode_get_swaps(slst_encode_context *context) {
  int i,j,k;
  poly_id interim[0x1000];
  poly_id_delta *delta;
  poly_id poly_id, tmp;
  int hi,lo,mid,l,r,top;
  int lo_stack[0x100], hi_stack[0x100];
 
  context->swap_count = 0;
  
  // build interim list using src list removes, dst list adds, 
  // and copies
  for (i=0,j=0;i<context->delta_count;i++) {
    delta = context->deltas[i];
    if (delta->op == -1) continue;
    if (delta->op == 1)
      poly_id = context->dst[delta->dst_idx];
    else
      poly_id = context->src[delta->src_idx];
    interim[j++] = poly_id;
  }
  
  // quicksort the interim list. record each swap in a new delta 
  lo = 0;
  hi = context->dst_len-1;
  top = 1;
  while (top) {
    mid = lo+((hi-lo)>>1);
    
    if (poly_id_swap_cmp(lo,mid))
      poly_id_swap(lo,mid);
    if (poly_id_swap_cmp(mid,hi)) {
      poly_id_swap(mid,hi);
    }
    else
      goto jump_over;
    if (poly_id_swap_cmp(lo,mid))
      poly_id_swap(lo,mid);
jump_over:  
    l = lo+1;
    r = hi-1;
    do {
      while (poly_id_swap_cmp(l,mid)) l++;
      while (poly_id_swap_cmp(mid,r)) r--;
      if (l<r) {
        poly_id_swap(l,r);
        if (mid==l) mid = r;
        else if (mid==r) mid = l;
        l++; r--;
      }
      else if (l==r) {
        l++; r--;
        break;
      }
    } while (l <= r);
    
    k = ((r-lo) <= 1) | (((hi-l) <= 1)<<1);
    switch(k) {
    case 0: 
      if ((r-lo)>(hi-l)) {
        lo_stack[top] = lo;
        hi_stack[top] = r;
        lo = l;
      }
      else {
        lo_stack[top] = l;
        hi_stack[top] = hi;
        hi = r;
      }
      top++;
      break;
    case 1: lo=l; break;
    case 2: hi=r; break;
    case 3: top--; break;
    }  
  }
}
*/

/**
 * the core slst encoding function
 * 
 * returns an slst entry item which delta encodes the differences 
 * between poly id lists src and dst
 * 
 * most of the code internal to this function simply converts the 
 * general deltas data generated by the other functions to the Crash 
 * format. the Crash format is more compact as it employs various 
 * compression techniques (mainly RLE for adjacent deltas and relative 
 * indexing). 
 */
slst *slst_encode(poly_id *src, poly_id *dst, int src_len, int dst_len,
		              size_t *slst_size) {
  int i;
  slst *slst;
  slst_context add, rem, swap;
  uint16_t add_nodes[0x1000], rem_nodes[0x1000], swap_nodes[0x1000];
  slst_encode_context context;
  poly_id poly_id;
  poly_id_delta *delta;
  int prev_op, prev_idx;
   
  context.src = src;
  context.dst = dst;
  context.src_len = src_len;
  context.dst_len = dst_len;

  slst_encode_init_map(&context);
  slst_encode_mark_copies(&context);
  slst_encode_mark_swaps(&context);
  slst_encode_get_deltas(&context);
  // slst_encode_get_swaps(&context);
  
  add.idx = 0;
  rem.idx = 0;
  add.len = 0;
  rem.len = 0;
  add.i = 0;
  rem.i = 0;
  swap.i = 0;
  add.count = 0;
  rem.count = 0;
  prev_idx = 0;
  prev_op = -2;
  delta = 0;
  for (i=0;i<=context.delta_count;i++) {
    // TODO:
    //       intermediary copy/add/removes
    //
    if (i<context.delta_count)
      delta = context.deltas[i];
    if ((delta && delta->op != prev_op) || i==context.delta_count || 
        rem.len >= 16 || add.len >= 16) {
      if (prev_op == -1 || prev_op == -3) {
        rem.idx = rem.i - (rem.len+1);
        rem_nodes[rem.idx] = ((rem.len-1) << 12) | (1+prev_idx);
        rem.len = 0;
      }
      else if (prev_op == 1 || prev_op == 3) {
        add.idx = add.i - (add.len+1);
        add_nodes[add.idx] = ((add.len-1) << 12) | (prev_idx-(add.count-add.len));
        add.len = 0;
      }
      if (i==context.delta_count) break; // concluding the last seq 
      if (delta->op == -1 || delta->op == -3) {
        rem.i++;
        prev_idx = delta->src_idx;
      }
      else if (delta->op == 1 || delta->op == 3) {
        add.i++;
        prev_idx = delta->dst_idx;
      }
    }
    if (delta->op == -1 || delta->op == -3) {
      poly_id = context.src[delta->src_idx];
      // poly_id.flag = 1;
      // TODO: poly_id_val macro removes flag; here it should not
      rem_nodes[rem.i++] = 0x8000 | poly_id_val(poly_id);
      rem.len++;
      rem.count++;
    }
    else if (delta->op == 1 || delta->op == 3) {
      poly_id = context.dst[delta->dst_idx];
      add_nodes[add.i++] = poly_id_val(poly_id);        
      add.len++;
      add.count++;
    }

    if (delta->op == 4) {
      if (delta->src_idx < delta->dst_idx) {
        swap.idx = delta->src_idx;
        swap.len = delta->dst_idx - delta->src_idx - 1;
      }
      else {
        swap.idx = delta->dst_idx;
        swap.len = delta->src_idx - delta->dst_idx - 1;
      }
      if (swap.len < 16) {
        ((slst_swap_fmta*)&swap_nodes[swap.i])->fmt = 1;
        ((slst_swap_fmta*)&swap_nodes[swap.i])->idx = swap.idx;
        ((slst_swap_fmta*)&swap_nodes[swap.i])->offset = swap.len;
        swap.i += sizeof(slst_swap_fmta)/sizeof(uint16_t);
      }
      else if (swap.len < 48 && (swap.idx-prev_idx) < 512) {
        ((slst_swap_fmtc*)&swap_nodes[swap.i])->fmt = 1;
        ((slst_swap_fmtc*)&swap_nodes[swap.i])->idx = swap.idx-prev_idx;
        ((slst_swap_fmtc*)&swap_nodes[swap.i])->offset = swap.len - 16;
        swap.i += sizeof(slst_swap_fmtc)/sizeof(uint16_t);
      } 
      else {
        ((slst_swap_fmtb*)&swap_nodes[swap.i])->fmt = 0;
        ((slst_swap_fmtb*)&swap_nodes[swap.i])->fmt_2 = 0;
        ((slst_swap_fmtb*)&swap_nodes[swap.i])->idx = swap.idx;
        ((slst_swap_fmtb*)&swap_nodes[swap.i])->offset = swap.len;
        swap.i += sizeof(slst_swap_fmtb)/sizeof(uint16_t);
      }
      prev_idx = swap.idx;
    }
    prev_op = delta->op;
  }
  
  rem.start = offsetof(slst_delta, data)/sizeof(slst->delta.data[0]);
  add.start = rem.end = rem.start + rem.i;
  swap.start = add.end = add.start + add.i;
  swap.end = swap.start + swap.i;
  
  *slst_size = sizeof(slst) + (swap.end*sizeof(slst->delta.data[0]));
  slst = malloc(*slst_size);
  
  memcpy(((uint16_t*)&slst->delta) + rem.start, rem_nodes,
    (rem.end - rem.start)*sizeof(slst->delta.data[0]));
  memcpy(((uint16_t*)&slst->delta) + add.start, add_nodes,
    (add.end - add.start)*sizeof(slst->delta.data[0]));
  memcpy(((uint16_t*)&slst->delta) + swap.start, swap_nodes,
    (swap.end - swap.start)*sizeof(slst->delta.data[0]));
      
  slst->type = 1;
  slst->length = swap.end;
  slst->delta.split_idx = add.start;
  slst->delta.swaps_idx = swap.start;   
 
  return slst;
}

/* 
 * inline slst_rem_next code for the inital call:
 * 
 * 
 * rem.node = nodes[rem.i++]; // process the next (i.e. first) removing node 
 * if (rem.i < add.start && rem.node != 0xFFFF) { 
 *   rem.idx = rem.node & 0xFFF;
 *   rem.len = ((rem.node & 0xF000) >> 12) + 1; // min 1
 * } 
 * else {
 *   rem.idx = 0xFFFF00; // null index
 *   rem.len = 0;        // no addition
 * }
 * 
 * if (rem.len > 0) 
 *   rem.poly = nodes[rem.i++]; // grab the first poly id in the sequence
 * else
 *   rem.poly = 0xFFFF;
 * 
 * 
 * inline slst_add_next code for initial call:
 * 
 * add.node = nodes[add.i++]; // process the next (i.e. first) adding node
 * if (add.i < swap && add.node != 0xFFFF) { 
 *   add.idx = add.node & 0xFFF;             
 *   add.len = ((add.node & 0xF000) >> 12) + 1; // min 1
 * }
 * else { 
 *  add.idx = 0xFFFF00;
 *  add.len = 0;
 * }
 *
 * if (add.len > 0)
 *   add.poly = nodes[add.i++]; // grab the first polyid in the sequence
 *   
 */ 

/**
*  
* // build delta encoded c-table
* for (i=0;i<idx_count;i++) {
*   if (lcs_count==0 || idxs[i]>c_col[lcs_count-1]) {
*     c_deltas[i] = -1;
*     c_idxs[i] = lcs_count;
*     c_col[lcs_count++] = idxs[i];
*     continue;
*   }
*       // binary search
*       j=0;
*       k=lcs_count;
*       while(k>1) {
*         r = (k&1);
*         k = (k>>1)+r; // k = ceil(k/2); pivot ctr, tend right for even
*         j += k;
*         if (idxs[i] == c_col[j]) break; // choose pivot if equal
*         if (idxs[i] > c_col[j]) k-=r; // if > pivot then recurse on r half
*         else j-=k; // else recurse on left half
*         if ((k==1) && (idxs[i]>c_col[j])) j++;
*       } 
*       c_deltas[i] = c_col[j];
*       c_idxs[i] = j;
*       c_col[j] = idxs[i];
* }
* 
* // backtrack
* j=idx_count-1;
* k=lcs_count-1;
* for (i=idx_count-1;i>=0;i--) {
*       r=j;
*   while (j > (c_col[c_idxs[i]]-1)  
*           && (c_deltas[i] == -1 || j < c_deltas[i]))
*         j--;
*       if (r!=j) lcs[k--] = i; 
*       if (c_deltas[i] != -1)
*         c_col[c_idxs[i]] = c_deltas[i];
*  }
*/


// (136, 3), (141, 2), (131, 2), (121, 3), (111, 2), (101, 3), (100, 2), (98, 2), (103, 2), (100, 3), (98, 3)
// (159, 3), (141, 3), (136, 3), (123, 3), (117, 2), (100, 2), (105, 3), (98, 2), (102, 3), 


// (159, 3), (141, 3), (136, 3), (123, 3), (


// add 159, 3        
// add 141, 3
// copy 136, 3
// remove 141, 2
// remove 131, 2
// remove 121, 3
// remove 111, 2
// remove 101, 3
// add 123, 3
// add 117, 2
// copy 100, 2
// add 105, 3
// copy 98, 2
// add 102, 3
// copy 103, 2
// copy 100, 3



// add: (0, 2, [(159, 3), (141, 3)]), (1, 2, [(123, 3), (117, 2)]), (2, 1, [(105, 3)]), (3, 1, [(102, 3)])

// rem: (2, 5, [(141, 2), (131, 2), (121, 3), (111, 2), (101, 3)]), 

// 4002


#include "page.h"
#include "misc/suffix_tree.h"

page *page_read(uint8_t *data) {
  int i;
  page *pg;
  entry *en;
  uint8_t *en_data;
  
  pg = data; // implicit cast
  if (pg->type == 1)
    return pg;
    
  for (i=0;i<pg->entry_count;i++) {
    en_data = (uint8_t*)pg + pg->entry_offsets[i];
    en = entry_read(en_data);
    
    pg->entries[i] = en;
  }
  
  return pg;
}

uint8_t *page_write(page *pg) {
  int i;
  uint8_t *data;
  entry *en;
  uint8_t *en_data;
  
  data = pg; // implicit cast
  if (pg->type == 1)
    return data;

  for (i=0;i<pg->entry_count;i++) {
    en = pg->entries[i];
    en_data = entry_write(en);
        
    pg->entry_offsets[i] = (uint32_t)(en_data - (uint8_t*)pg);
  }
  
  return data;
}

void page_decompress(page *page_dst, page_compressed *page_src) {
  int i, size;
  uint16_t seek, length, skip, remainder;
  uint8_t data, span, prefix;
  uint8_t *src, *dst;
  
  src = page_src->data;
  dst = (uint8_t*)page_dst;
  while (dst - (uint8_t*)page_dst < page_src->length) {
    prefix = *(src++);
    if (prefix & 0x80) {
      data = *(src++);
      span = data & 7; 
      seek = ((prefix & 0x7F) << 5) | (data >> 3);
      if (span == 7)
        span = 0x40;
      else
        span += 3;
      for (i=0;i<span;i++,dst++)
        *(dst) = *(dst - seek);
      dst += span;
    }
    else {
      memcpy(dst, src, prefix);
      src += prefix;
      dst += prefix;
    }
  }
  src += page_src->skip;
  
  remainder = PAGE_SIZE - page_src->length;
  memcpy(dst, src, remainder);
//  return size + remainder;
}

void page_compress(page *page_src, page_compressed *page_dst) {
  int i, ii, len;
  uint16_t seek;
  uint8_t data, span, prefix;
  uint8_t *src, *dst, *ahead;
  uint8_t *ptrs[0x8000];
  suffix_tree *tree;
  trie_node *node, *seq;
  uint32_t length, count, offset;
  
  tree = (suffix_tree*)malloc(sizeof(suffix_tree));
  suffix_tree_init(tree);
  
  page_dst->length = PAGE_SIZE;
  page_dst->skip = 0;
  
  span = 0;
  prefix = 0;
  count = 0;
  src = (uint8_t*)page_src;
  dst = page_dst->data;
  seq = 0;
  for (i=0;i<PAGE_SIZE;i++) {
    /*
    while (dst-page_dst->data > 64 && i <= PAGE_SIZE-64) {
      for (ii=0;ii<64;ii++)
        if (*(dst-64+ii)!=*(src+ii)) break;
        if (ii!=64) break;
        *(dst++) = 130; *(dst++) = 7;
        src += 64; 
        i += 64;
      }
    */
    if (i>8) suffix_tree_insert(tree, *(src-9), i-9);
    data = *(src++);
retry:  
    if (span==0) seq = tree->root;
    if (node = i<9?0:suffix_tree_find_child(seq, data)) {
      seq = node;
      span++;
    }
    if (node && span <= 9) continue;
    if (span <= 2) {
      prefix += (span + 1);
      span = 0;
    }
    else {
      // seek = i-(2*span+seq->idx+1);
      seek = i-(seq->idx+1);
      while (prefix != 0) {
        ptrs[count++] = dst;
	*(dst++) = len = min(127,prefix);
        for (ii=prefix+span+1;ii>prefix+span+1-len;ii--)
          *(dst++) = *(src-ii);
        prefix -= len;
      }
      ptrs[count++] = dst;
      *(dst++) = 0x80 | ((seek >> 5) & 0x7F);
      *(dst++) = (seek << 3) | (span - 3);
      
      span = 0;
      if (!node) goto retry;
    }
  }  
  ptrs[count] = dst;
  // if a copy op would have ended the sequence or otherwise the last 
  // op as a compression op did not finish and was not committed, then 
  // rewind src so that the corresponding bytes are instead direct 
  // copied in the next stage
  src -= (prefix + span);

  length = (uint32_t)(dst - (uint8_t*)page_dst) + (prefix + span);
  offset = sector_offset(length);
  
  for (i=count-1;i>=0;i--) {
    span = ptrs[i][0];
    if (span & 0x80) {
      data = ptrs[i][1];
      span = (data & 7) + 3; 
      // if (span == 10) span = 0x40;
      if (offset+(span-2) > SECTOR_SIZE)
        break;
      offset += (span-1);
    }
    offset--;
    src -= span;
  }
  dst = ptrs[i+1];

  page_dst->magic = MAGIC_COMPRESSED;
  page_dst->length = (uint32_t)(src - (uint8_t*)page_src);
  page_dst->skip = SECTOR_SIZE - offset;
  
  dst += page_dst->skip;
  memcpy(dst, src, PAGE_SIZE - page_dst->length);

  free(tree);  
}

size_t page_compressed_size(page_compressed *page_src) {
  uint8_t *src;
  uint8_t span, data;
  uint16_t remainder;
  size_t size, compressed_size;
  
  size = 0;
  src = page_src->data;
  while (size < page_src->length) {
    span = *(src++);
    if (span & 0x80) {
      data = *(src++);
      span = (data & 7) + 3; 
      // if (span == 10) span = 0x40;
    }
    else
      src += span;
    size += span;
  }
  src += page_src->skip;
  remainder = PAGE_SIZE - page_src->length;
  src += remainder;
  
  compressed_size = src - (uint8_t*)page_src;
  return compressed_size;
}


// pages in the nsd is a pointer to the contiguous pages, so a page of 
// the full size must be maintained if unpacking any single one.
// we generally should not have to worry about manually packing and 
// unpacking pages unless there is a specific existing page for which
// to add/remove/reorder entry data. otherwise nsf_new should handle the
// packing automatically from the nsd 
page *page_unpack(page *pg, int flags) {
  int i;
  size_t page_size;
  entry *en;
  size_t en_size;
  uint8_t *en_data;
   
  for (i=0;i<pg->entry_count;i++) {
    en = pg->entries[i];
    entry_write(en);
    en_size = en->item_offsets[en->item_count];
    en_data = malloc(en_size);
    memcpy(en_data, en, en_size);
    en = (entry*)en_data;
    entry_read(en);
    pg->entries[i] = en;
  }
  if (flags & 1) {
    page_size = offsetof(page, entries) + pg->entry_count*sizeof(entry*);
    pg = realloc(pg, page_size);
  }
  return pg;
}

page *page_pack(page *pg, int flags) {
  int i;
  size_t page_size;
  entry *en;
  size_t en_size;
  uint8_t *en_data;
  
  page_size = offsetof(page, entries) + pg->entry_count*sizeof(entry*);
  for (i=0;i<pg->entry_count;i++) {
    en = pg->entries[i];
    en_size = (size_t)(en->items[en->item_count] - (uint8_t*)en);
    page_size += en_size;
    if (page_size > PAGE_SIZE)
      return 0;
  }
  for (i=0;i<pg->entry_count;i++) {
    en = pg->entries[i];
    entry_write(en);
  }
  if (flags & 1) {
    pg = realloc(pg, PAGE_SIZE);  
  }
  page_size = offsetof(page, entries) + pg->entry_count*sizeof(entry*);
  en_data = (uint8_t*)pg + page_size;
  for (i=0;i<pg->entry_count;i++) {
    en = pg->entries[i];
    en_size = en->item_offsets[en->item_count];
    memcpy(en_data, en, en_size);
    free(en);
    en = (entry*)en_data;
    entry_read(en);
    pg->entries[i] = en;
    en_data += en_size;
  }
  
  return pg;
}

page *page_init(page *pg, int idx) {
  pg->magic = MAGIC_PAGE;
  pg->type = 0;
  pg->pgid = (pgid_t)((idx << 1) | 1);
  pg->entry_count = 0;
  
  return pg;
}

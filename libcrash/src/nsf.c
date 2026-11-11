#include "nsf.h"

nsf *nsf_read(uint8_t *data, nsd *nsd) {
  int i;
  uint32_t offset;
  nsf *nsf;
  
  nsf = data; // implicit cast
  nsd->pages = (page*)&data[nsd->pages_offset*0x800];
  for (i=0;i<nsd->compressed_page_count;i++) {
    offset = nsd->compressed_page_offsets[i]*0x800;
    nsd->compressed_pages[i] = (page*)&data[offset];
  }
  for (i=0;i<nsd->page_count;i++) {
    page_read((uint8_t*)&nsd->pages[i]);
  }
  
  nsf->dir = nsd;
  return nsf;
}

uint8_t *nsf_write(nsf *nsf, nsd *nsd, size_t *size) {
  int i;
  uint32_t offset;
  uint8_t *data;
  
  data = nsf; // implicit cast
  for (i=0;i<nsd->page_count;i++) {
    page_write(&nsd->pages[i]);
  }
  for (i=0;i<nsd->compressed_page_count;i++) {
    offset = (uint32_t)((uint8_t*)nsd->compressed_pages[i] - data);
    nsd->compressed_page_offsets[i] = offset/0x800;
  }
  if (size)
    *size = (uint8_t*)(nsd->pages) + 
      (nsd->page_count*PAGE_SIZE) - nsf->data;
  nsd->pages_offset = (uint32_t)((uint8_t*)nsd->pages - data)/0x800;
  
  nsf->dir = MAGIC_COMPRESSED;

  return data;
}

page *nsf_page(nsf *nsf, pgid_t pgid) {
  int idx;
  page *page;
  
  idx = (pgid >> 1);
  page = &nsf->dir->pages[idx];
  
  return page;
}

page *nsf_texture_page(nsf *nsf, eid_t eid) {
  int i;
  page *page;
  
  page = 0;
  for (i=0;i<nsf->dir->page_count;i++) {
    if (page->type == 1 && page->pgid == eid)
      break;
  }
  
  return page;
}

/*
entry *nsf_entry(nsf *nsf, eid_t eid) { 
  pgid_t pgid;
  entry *entry;
  
  pgid = nsd_lookup_pgid(nsf->dir, eid);
  entry = _nsf_entry(nsf, eid, pgid);
  
  return entry; 
}
*/

entry *nsf_entry(nsf *nsf, eid_t eid) {
  nsd_pte *pte;
  
  pte = nsd_lookup(nsf->dir, eid);
  if (pte->key & 1)
    pte->entry = _nsf_entry(nsf, eid, pte->pgid);
    
  return pte->entry;
}

entry *_nsf_entry(nsf *nsf, eid_t eid, pgid_t pgid) {
  int i;
  page *page;
  entry *en;
  
  page = nsf_page(nsf, pgid);
  if (page->type == 1) {
    return (entry*)page;
  }
  en = 0;
  for (i=0;i<page->entry_count;i++) {
    en = page->entries[i];
    if (en->eid == eid)
      break;
  }
  
  return en;
}

int nsf_entry_idx(nsf *nsf, eid_t eid, pgid_t pgid) {
  int i;
  page *page;
  entry *entry;
  
  page = nsf_page(nsf, pgid);
  for (i=0;i<page->entry_count;i++) {
    entry = page->entries[i];
    if (entry->eid == eid)
      return i;
  }
  
  return -1;
}

page *nsf_page_new(nsf *nsf, int flags) {
  int idx;
  page *page;
  size_t size;
  
  idx = nsf->dir->page_count++;
  if (flags & 1) {
    // todo: realloc probably won't work unless we pre-write and post-read
    size = (uint8_t*)&nsf->dir->pages[idx+1] - (uint8_t*)nsf;
    nsf = realloc(nsf, size);
  }
  page = &nsf->dir->pages[idx];
  page_init(page, idx);
  
  return page;
}

/**
 * packs the contents of entries referenced in the page table into a 
 * contiguous region of pages
 * 
 * nsd - nsd with page table
 * pages - pre-allocated block of size sufficient to fit the pages
 * 
 * returns - number of pages 
 * 
 * note: it is possible to calculate the number of pages/minimum size
 *       of the block in advance, however to keep things simple for now
 *       we expect a maximal sized allocated region
 */
static inline int nsf_new_pack_entries(nsd *nsd, page *pages) {
  int i, ii;
  entry *en;
  nsd_pte *pte;
  size_t page_sizes[256];
  size_t en_size;
  int page_count;

  #define PAGE_HEADER_SIZE \
    (offsetof(page, entries) + sizeof(entry*)*PAGE_ENTRIES_MAX)
        
  page_sizes[0] = PAGE_HEADER_SIZE;
  page_init(&pages[0], 0);
  page_count = 1;
  for (i=0;i<nsd->page_table_size;i++) {
    pte = &nsd->page_table[i];
    if (pte->key & 1) {
      return 0;
    }
    en = pte->entry;
    en = entry_pack(en, 1); // not [necessarily] in-place
    en_size = entry_size(en);
    if (en_size > PAGE_SIZE) {
      return 0;
    }
    for (ii=0;ii<page_count;ii++)
      if (page_sizes[ii] + en_size < PAGE_SIZE) break;
    if (ii == page_count) {
      page_sizes[page_count] = PAGE_HEADER_SIZE;
      page_init(&pages[page_count], page_count);
      page_count++;
      if (page_count > 256) {
        return 0;
      }
    }
    page_sizes[ii] += en_size;
    pages[ii].entries[pages[ii].entry_count++] = en;
  
    pte->pgid = pages[ii].pgid;
    pte->eid = en->eid; // replace pointer with id, mem will be moved
  }
  return page_count;
}

/**
 * compresses pages. calculates the size of a contiguous block of 
 * compressed pages with the N highest ratios or otherwise the maximum 
 * number of highest ratio pages with total size below M.
 * 
 * pages - pages to compress
 * page_count - number of pages
 * pages_compressed - pre-allocated block of size sufficient to fit the
 *                    compressed pages
 * sorted - (out) pointers to compressed pages in order of compression 
 *                ratio
 * count - (out) number of compressed pages from the start of 'sorted' 
 *               such that have the largest total size below M, or N
 * size - (out) total size of contiguous block of the first 'count' 
 *              sorted compressed pages
 */
static inline 
void nsf_new_compress_pages(page *pages, int page_count,
                            page_compressed *pages_compressed,
                            page_compressed **sorted,
                            int *count, size_t *size) { 
  int i,j,k;
  int compressed_size;
  page_compressed *compressed;
  
  compressed = pages_compressed;
  for (i=0;i<page_count;i++) {
    page_compress(&pages[i], compressed);
    compressed->magic = page_compressed_size(compressed);
    for (j=0;j<i;j++) {
      if (compressed->magic < sorted[j]->magic) {
        for (k=i;k>j;k--) sorted[k] = sorted[k-1];
        break;
      }
    }
    sorted[j] = compressed;
    compressed += compressed->magic;
  }

  // 32 = NSF_PAGES_COMPRESSED_MAX
  *size = 0;
  *count = 0;
  for (i=0;i<min(page_count,32);i++) {
    compressed_size = sorted[i]->magic;
    sorted[i]->magic = 0x1235;
    // if (*size + length > 0x10000) break;
    *size += compressed_size;
    (*count)++;
  }
}

/**
 * creates a new nsf from the nsd page table entries
 * 
 * packs the contents of entries referenced in the page table into a 
 * contiguous region of pages, compresses those pages, and prepends a 
 * contiguous region of the most optimal compressed pages. 
 * then points the nsd to the new pages (compressed and uncompressed)
 * 
 * returns - pointer to the nsf data, i.e. the region of compressed 
 *           pages followed by [uncompressed] pages
 * 
 * note: might want 'distribute entries' functionality for an existing 
 *       nsf...
 */
nsf *nsf_new(nsd *nsd) {
  int i;
  nsf *nsf;
  page *pages;
  int page_count;
  page_compressed *compressed_pages;
  page_compressed *sorted[256];
  int compressed_count;
  size_t size, compressed_size;
  uint8_t *data, *dst;
  
  pages = (page*)malloc(PAGE_SIZE*256);
  page_count = nsf_new_pack_entries(nsd, pages);
  if (!page_count) {
    free(pages);
    return 0;
  }
  for (i=0;i<page_count;i++) {
    page_pack(&pages[i], 0); // in-place
    page_write(&pages[i]); // we are compressing relative offsets
  }
  
  compressed_pages = (page_compressed*)malloc(PAGE_SIZE*256);
  nsf_new_compress_pages(pages, page_count, compressed_pages, &sorted, 
                         &compressed_count, &compressed_size);
  
  data = malloc(compressed_size + page_count*PAGE_SIZE);
  dst = data;
  for (i=0;i<compressed_count;i++) {
    size = page_compressed_size(sorted[i]);
    memcpy(dst, sorted[i], size);
    nsd->compressed_pages[i] = (page_compressed*)dst;
    dst += size;
  }
  memcpy(dst, pages, page_count*PAGE_SIZE); 
  nsd->pages = (page*)dst;
  dst += page_count*PAGE_SIZE;
  for (i=0;i<page_count;i++)
    page_read(&nsd->pages[i]); // convert relative offsets back to ptrs
    
  nsd->page_count = page_count;
  nsd->compressed_page_count = compressed_count;
  
  nsf = data;
  nsf->dir = nsd;
  
  free(pages);
  free(compressed_pages);

  return nsf;
}

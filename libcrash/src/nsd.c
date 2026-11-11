#include "nsd.h"

nsd *nsd_read(uint8_t *data) {
  int i,idx;
  nsd *nsd; 
  
  nsd = data; // implicit cast
  for (i=0;i<NSD_PTB_MAX;i++) {
    idx = nsd->ptb_offsets[i];
    nsd->page_table_buckets[i] = &nsd->page_table[idx];
  }
  
  return nsd;
}

uint8_t *nsd_write(nsd *nsd, size_t *size) {
  int i,idx;
  uint8_t *data;
  
  for (i=0;i<NSD_PTB_MAX;i++) {
    idx = nsd->page_table_buckets[i] - nsd->page_table;
    nsd->ptb_offsets[i] = idx;
  }
  for (i=0;i<nsd->page_table_size;i++) {
	if (!(nsd->page_table[i].key & 1))
	  nsd->page_table[i].eid = nsd->page_table[i].entry->eid;
  }
  data = nsd;
  
  if (size)
    *size = ((uint8_t*)nsd_ldat(nsd) - (uint8_t*)(nsd)) 
          + sizeof(nsd_ldat); 
  return data;
}

/** 
 * unpacks an nsd
 * 
 * nsd - packed nsd
 * page_table_len - amount of memory to reserve for the page table, in
 *                  units of ptes. 0 specifies the default (NSD_MAX_PTE)
 * ldat - (out) unpacked ldat
 * 
 * returns - unpacked nsd
 * 
 * realloc is mandatory
 */
nsd *nsd_unpack(nsd *_nsd, int page_table_len, nsd_ldat *ldat) {
  size_t nsd_size;
  
  nsd_size = ((uint8_t*)nsd_ldat(_nsd) - (uint8_t*)_nsd);
  ldat = (nsd_ldat*)malloc(sizeof(nsd_ldat));
  memcpy(ldat, nsd_ldat(_nsd), sizeof(nsd_ldat));
  
  if (page_table_len == 0) 
    page_table_len = NSD_PTE_MAX;
  nsd_size = sizeof(nsd) + page_table_len*sizeof(nsd_pte);
  _nsd = realloc(_nsd, nsd_size);
  
  return _nsd;
}

nsd *nsd_pack(nsd *_nsd, nsd_ldat *ldat) {
  size_t nsd_size, size;
  
  nsd_size = ((uint8_t*)nsd_ldat(_nsd) - (uint8_t*)_nsd);
  size = nsd_size + sizeof(nsd_ldat);
  
  _nsd = realloc(_nsd, size);
  memcpy(nsd_ldat(_nsd), ldat, sizeof(nsd_ldat));
  
  return _nsd;
}
      
nsd_pte *nsd_lookup(nsd *nsd, eid_t eid) {
  int idx, i;
  nsd_pte *bucket;
  
  if (eid == EID_NONE) { return (nsd_pte*)0; }
  idx = (eid >> 15) & 0xFF;
  bucket = nsd->page_table_buckets[idx];
  
  for (i=0;i<NSD_PTE_MAX;i++) {
    if (bucket[i].key & 1) {
	  if (eid == bucket[i].eid)
        return &bucket[i];
    }
    else if (bucket[i].entry->eid == eid)
      return &bucket[i];
  }
  
  return (nsd_pte*)0;
}

pgid_t nsd_lookup_pgid(nsd *nsd, eid_t eid) {
  nsd_pte *pte;
  
  pte = nsd_lookup(nsd, eid);
  if (pte)
    return pte->pgid;
  
  return (pgid_t)0;
}

eid_t nsd_global_eid(nsd *_nsd, int idx) {
  nsd_ldat* ldat;
  
  ldat = nsd_ldat(_nsd);
  
  return ldat->exec_map[idx];
}

int nsd_global_eid_idx(nsd *_nsd, eid_t eid) {
  int i;
  nsd_ldat* ldat;
  
  ldat = nsd_ldat(_nsd);
  
  for (i=0;i<NSD_GLEID_MAX;i++) {
    if (eid == ldat->exec_map[i]) {
      return i;
    }
  }
  return -1;
}

nsd *nsd_alloc(int page_table_len) {
  nsd *_nsd;
  size_t nsd_size;
  
  nsd_size = sizeof(nsd) + page_table_len*(sizeof(nsd_pte));
  _nsd = malloc(nsd_size); 
  
  return _nsd;
}

nsd *nsd_init(nsd *nsd) {
  int i;
  
  nsd->page_count = 0;
  nsd->compressed_page_count = 0;
  nsd->page_table_size = 0;
  memset(&nsd->page_table_buckets, 0, sizeof(nsd->page_table_buckets));
  nsd_read((uint8_t*)nsd);
  
  return nsd;
}

nsd *nsd_new(int page_table_len) {
  nsd *nsd;
  
  nsd = nsd_alloc(page_table_len);
  nsd_init(nsd);
  
  return nsd;
}

nsd_pte *nsd_pte_new(nsd *nsd, entry *en, pgid_t pgid) {
  int i,idx,pte_idx;
  size_t nsd_size;
  nsd_pte *pte;
  nsd_pte *bucket_end;
    
  idx = (en->eid >> 15) & 0xFF;
  bucket_end = nsd->page_table_buckets[idx+1];
  pte_idx = (int)(bucket_end - nsd->page_table);
  nsd->page_table_size++;
  for (i=pte_idx+1;i<nsd->page_table_size;i++) {
    nsd->page_table[i] = nsd->page_table[i-1];
  }
  for (i=idx+1;i<NSD_PTB_MAX;i++) {
	  nsd->page_table_buckets[i]++;
  }
  pte = &nsd->page_table[pte_idx];
  pte->entry = en;
  pte->pgid = pgid;
  
  return pte;
}

entry *nsd_entry_new(nsd *nsd, eid_t eid, int type, int item_count) {
  entry *en;
  
  en = entry_alloc(item_count);
  entry_init(en, eid, type);
  nsd_pte_new(nsd, en, 0);
  
  return en;
}

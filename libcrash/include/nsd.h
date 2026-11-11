#ifndef NSD_H
#define NSD_H

#include "types.h"
#include "page.h"
#include "entry.h"

#define MAGIC_LDAT 1  // for now

#define NSD_GLEID_MAX 64

#ifndef ID_STRUCTS
typedef uint32_t lid_t;
#else
typedef struct { uint32_t value; } lid_t;
#endif

typedef struct {
  uint32_t magic;
  lid_t lid;
  eid_t zone_spawn;
  uint32_t path_spawn;
  unk32_t unk_10;
  eid_t exec_map[NSD_GLEID_MAX];
  uint32_t screen_proj;
  uint8_t image_data[0xF5F8];
} nsd_ldat;

#define NSD_PTE_MAX 256
#define NSD_PTB_MAX 256

typedef struct {
  union {
    pgid_t pgid;
    uint32_t value;
  };
  union {
    eid_t eid;
    entry *entry;
    uint32_t key;
  };
} nsd_pte;
    
typedef struct {
  union {
    uint32_t ptb_offsets[NSD_PTB_MAX];
    nsd_pte* page_table_buckets[NSD_PTB_MAX];
  };
  int32_t page_count;
  size_t page_table_size;
  eid_t unk_0x408;
  unk32_t unk_0x40C;
  unk32_t unk_0x410;
  unk32_t unk_0x414;
  union {
    uint32_t pages_offset;
    page *pages;
  };
  int32_t compressed_page_count;
  union {
    uint32_t compressed_page_offsets[64];
    uint8_t *compressed_pages[64];
  };
  nsd_pte page_table[];
} nsd;

#define nsd_ldat(_nsd) \
  (nsd_ldat*)((uint8_t*)_nsd \
    + sizeof(nsd) \
    + sizeof(nsd_pte)*_nsd->page_table_size)
           
extern nsd *nsd_read(uint8_t *data);
extern uint8_t *nsd_write(nsd *nsd, size_t *size);

extern nsd *nsd_unpack(nsd *nsd, int page_table_len, nsd_ldat *ldat);
extern nsd *nsd_pack(nsd *nsd, nsd_ldat *ldat);

extern nsd_pte *nsd_lookup(nsd *nsd, eid_t eid);
extern pgid_t nsd_lookup_pgid(nsd *nsd, eid_t eid);
extern eid_t nsd_global_eid(nsd *nsd, int idx);
extern int nsd_global_eid_idx(nsd *nsd, eid_t eid);

extern nsd *nsd_alloc(int page_table_len);
extern nsd *nsd_init(nsd *nsd);
extern nsd *nsd_new(int page_table_len);

// extern nsd_pte *nsd_pte_new(nsd *nsd, entry *en, pgid_t pgid);
extern entry *nsd_entry_new(nsd *nsd, eid_t eid, int type, int);

#endif

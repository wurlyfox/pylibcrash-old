#ifndef PAGE_H
#define PAGE_H

#include "types.h"
#include "entry.h"

#define MAGIC_PAGE 0x1234
#define MAGIC_COMPRESSED 0x1235
#define MAGIC_DECOMPESSED 0x8765

#define PAGE_SIZE 0x10000
#define PAGE_ENTRIES_MAX 256

#define SECTOR_SIZE 0x800

#define align_to_sectors(offset) \
  (((((uint32_t)(offset)-1)>>11)+1)<<11)
#define sector_offset(offset) \
  ((uint32_t)(offset)%(1<<11))
  
#ifndef ID_STRUCTS
typedef uint32_t pgid_t;
#else
typedef struct { uint32_t value; } pgid_t;
#endif

/*
 * There is no simple representation for the variable length list of
 * entry offsets and following entry data in pages. For now the offsets 
 * will occupy the first entry_count 32 bit values of _entry_data. The 
 * remainder of _entry_data will contain the actual entry data. 
 * 
 * _entry_data is never used directly and only exists to fill the 
 * remainder of the structure so that it occupies exactly PAGE_SIZE 
 * bytes of memory.
 */
typedef struct {
  uint16_t magic;
  uint16_t type;
  pgid_t pgid;
  uint32_t entry_count;
  uint32_t checksum;
  union {
    uint32_t entry_offsets[0];
    entry *entries[0];
  };
  uint8_t _entry_data[PAGE_SIZE-16];
} page;

typedef struct {
  uint16_t magic;
  uint16_t pad;
  uint32_t length;
  uint32_t skip;
  uint8_t data[];
} page_compressed;

typedef struct {
  union {
    struct {
      uint16_t magic;
      uint16_t type;
      eid_t eid;
      uint32_t entry_type;
      uint32_t checksum;
    };
    uint8_t data[PAGE_SIZE];
  };
} tpage;

extern page *page_read(uint8_t *data);
extern uint8_t *page_write(page *pg);

extern void page_decompress(page *page_dst, page_compressed *page_src);
extern void page_compress(page *page_src, page_compressed *page_dst);
extern size_t page_compressed_size(page_compressed *page_src);

extern page *page_unpack(page *pg, int flags);
extern page *page_pack(page *pg, int flags);

extern page *page_init(page *pg, int idx);

#endif

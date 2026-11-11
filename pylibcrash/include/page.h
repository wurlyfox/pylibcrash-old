typedef struct { uint32_t value; } pgid_t;
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
  uint8_t _entry_data[0x10000 -16];
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
    uint8_t data[0x10000];
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

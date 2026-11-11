typedef struct { uint32_t value; } eid_t;
typedef struct {
  union {
    uint32_t magic;
    size_t *item_sizes;
  };
  eid_t eid;
  uint32_t type;
  uint32_t item_count;
  union {
    uint32_t item_offsets[0];
    uint8_t *items[0];
  };
} entry;
extern entry *entry_read(uint8_t *data);
extern uint8_t *entry_write(entry *en);
extern entry *entry_unpack(entry *en, int flags);
extern entry *entry_pack(entry *en, int flags);
extern entry *entry_alloc(int item_count);
extern entry *entry_init(entry *en, eid_t eid, int type);
extern size_t entry_size(entry *en);
extern size_t entry_item_size(entry *en, int idx);
extern void eid_str(char *str, eid_t eid);
extern void str_eid(char *str, eid_t *eid);

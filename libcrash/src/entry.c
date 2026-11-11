#include "entry.h"
                    
entry *entry_read(uint8_t *data) {
  entry *en;
  int i;
  
  en = data; // implicit cast
  for (i=0;i<en->item_count+1;i++) {
    en->items[i] = &data[en->item_offsets[i]];
  }
  
  return en;
}

uint8_t *entry_write(entry *en) {
  uint8_t *data;
  int i;
  
  data = en; // implicit cast
  for (i=0;i<en->item_count+1;i++) {
    en->item_offsets[i] = (uint32_t)(en->items[i] - data);
  }
  
  return data;
}

size_t entry_size(entry *en) {
  size_t size;
  int i;
  
  if (en->magic == MAGIC_ENTRY)
    size = (size_t)(en->items[en->item_count] - (uint8_t*)en);
  else {
	  size = sizeof(entry) + (en->item_count+1)*sizeof(uint8_t*);
    for (i=0;i<en->item_count;i++)
	    size += en->item_sizes[i];
  }
  
  return size;
}

size_t entry_item_size(entry *en, int idx) {  
  size_t size;
  
  if (en->magic == MAGIC_ENTRY)
    size = (size_t)(en->items[idx+1] - en->items[idx]);
  else
    size = en->item_sizes[idx];
    
  return size;
}

entry *entry_unpack(entry *en, int flags) {
  int i;
  size_t en_size;
  uint8_t *item_data;
  size_t *item_sizes;
  
  item_sizes = (size_t*)malloc(en->item_count*sizeof(size_t));
  for (i=0;i<en->item_count;i++) {
	  item_sizes[i] = (size_t)(en->items[i+1] - en->items[i]);
	  item_data = (uint8_t*)malloc(item_sizes[i]);
    memcpy(item_data, en->items[i], item_sizes[i]);
    en->items[i] = item_data;
  }
  if (flags & 1) {
    en_size = sizeof(entry) + en->item_count*sizeof(uint8_t*);
    en = realloc(en, en_size); // does not include last pointer (no +1)
  }
  en->item_sizes = item_sizes;
  
  return en;
}

entry *entry_pack(entry *en, int flags) {
  int i;
  size_t en_size; 
  uint8_t *item_data;
    
  if (flags & 1) {
    en_size = sizeof(entry) + (en->item_count+1)*sizeof(uint8_t*);
    for (i=0;i<en->item_count;i++)
      en_size += en->item_sizes[i];
    en = realloc(en, en_size);
  }
  en_size = sizeof(entry) + (en->item_count+1)*sizeof(uint8_t*);
  item_data = (uint8_t*)en + en_size;
  for (i=0;i<en->item_count;i++) {
	  memcpy(item_data, en->items[i], en->item_sizes[i]);
	  free(en->items[i]);
	  en->items[i] = item_data;
	  item_data += en->item_sizes[i];
  }
  en->items[en->item_count] = item_data;
  free(en->item_sizes);
  
  en->magic = MAGIC_ENTRY;
  return en;
}

entry *entry_alloc(int item_count) {
  size_t en_size;
  entry *en;
  
  en_size = sizeof(entry) + sizeof(uint8_t*)*item_count;
  en = (entry*)malloc(en_size);
  en->item_sizes = (size_t*)malloc(sizeof(size_t)*item_count);
  en->item_count = item_count;
  
  return en;
}

entry *entry_init(entry *en, eid_t eid, int type) {
  en->eid = eid;
  en->type = type;
  
  return en;
}

static const char eid_alpha[] = { 
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
  'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
  'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D',
  'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
  'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
  'Y', 'Z', '_', '!' 
};

void eid_str(char *str, eid_t eid) {
  int i, idx, shift;

  shift = 1;
  for (i=0;i<5;i++,shift+=6) {
    idx = (eid >> shift) & 0x3F;
    str[4-i] = eid_alpha[idx];
  }
  str[5] = '\0';
}

void str_eid(char *str, eid_t *eid) {
  int i, idx, shift;
  
  shift = 1;
  *eid = 1;
  for (i=0;i<5;i++,shift+=6) {
    for (idx=0;idx<sizeof(eid_alpha);idx++) {
      if (eid_alpha[idx]==str[4-i])
        break;
    }
    *eid |= (idx << shift);
  }
}

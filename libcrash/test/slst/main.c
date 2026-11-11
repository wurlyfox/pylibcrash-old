#include <stdio.h>
#include <stdint.h>

#include "nsf.h"
#include "misc/slst_stats.h"

void *file_read(char* filename, size_t *size) {
  FILE *file;
  void *data;
        
  file = fopen(filename, "rb");
  fseek(file, 0, SEEK_END);
  *size = ftell(file);
  data = (void*)malloc(*size);
    
  fseek(file, 0, SEEK_SET);
  fread(data, *size, 1, file);
  fclose(file);
    
  return data;
}

void test(nsf *nsf) {
  entry *entry;
  eid_t eid;
  char str[6];
  char stats[100000];
  poly_id src[10000], dst[10000];
  int src_len, dst_len;
  slst* raw;
  int i;
  
  str_eid("e009S", &eid); 
  entry = nsf_entry(nsf, eid);

  eid_str(&str, entry->eid);
  printf("eid: %s\n", str);

  raw = entry->items[0];
  src_len = raw->length;
  memcpy(src, raw->poly_ids, src_len*sizeof(poly_id));

  for (i=1;i<entry->item_count-1;i++) {
    slst_stats_summary(entry, i, src, dst, src_len, &dst_len, stats);
    printf("%s\n", stats);

    memcpy(src, dst, dst_len*sizeof(poly_id));
    src_len = dst_len;
  }
  
  raw = entry->items[entry->item_count-1];
  src_len = raw->length;
  slst_stats_poly_ids(raw->poly_ids, src_len, stats);
  printf("%s\n", stats);
}
                
int main(int argc, char **argv) {
  char *filename;
  void *data;
  size_t size;
  nsf *nsf;
  nsd *nsd;

  filename = argv[1];
  data = file_read(filename, &size);
  nsd = nsd_read(data);
  filename[11] = 'F';
  data = file_read(filename, &size);
  nsf = nsf_read(data, nsd);

  test(nsf);

  return 0;
}       

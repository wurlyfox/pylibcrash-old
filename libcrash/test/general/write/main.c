#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>

#include "nsf.h"

void file_write(char* filename, void *data, size_t size) {
  FILE *file;
    
  file = fopen(filename, "wb");
  fwrite(data, 1, size, file);
  fclose(file);
}

void test(nsf **nsf, nsd **nsd) {
  int i, ii, iii;
  entry *en;
  eid_t eid;
  char str[6];
  uint8_t *item;
  size_t item_size;
  nsd_ldat ldat;
   
  time_t t;
  srand((unsigned)time(&t));
    
  *nsd = nsd_new(100);
  for (i=0;i<100;i++) {
    sprintf(str, "e%03xR", i+1);
    str_eid(str, &eid);
    en = nsd_entry_new(*nsd, eid, 0, 100);
    for (ii=0;ii<32;ii++) {
      item_size = rand() % 256; 
      item = (uint8_t*)malloc(item_size);
      for (iii=0;iii<item_size;iii++) {
        item[iii] = rand() % 8;
      }
      en->items[en->item_count] = item;
      en->item_sizes[en->item_count] = item_size;
      en->item_count++; 
    }
  }
  
  // simple ldat for now, just testing page packing and compression
  memset(&ldat, 0, sizeof(nsd_ldat));
  ldat.magic = 1;
  ldat.lid = 1;
  ldat.screen_proj = 0x5A;
  
  *nsf = nsf_new(*nsd);
  *nsd = nsd_pack(*nsd, &ldat);
}
       
int main(int argc, char **argv) {
  char *filename;
  void *data;
  size_t nsf_size, nsd_size;
  nsf *nsf;
  nsd *nsd;
    
  test(&nsf, &nsd);
   
  filename = argv[1];
  filename[11] = 'F';
  data = nsf_write(nsf, nsd, &nsf_size);
  file_write(filename, data, nsf_size);
  filename[11] = 'D';
  data = nsd_write(nsd, &nsd_size);
  file_write(filename, data, nsd_size);
    
  return 0;
}   

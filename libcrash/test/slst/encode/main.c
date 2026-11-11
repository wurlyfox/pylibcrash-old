#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>

#include "nsf.h"
#include "misc/slst_stats.h"

#define LIST_LENGTH 200
#define LIST_COUNT 10
#define LIST_SIZE (sizeof(poly_id)*LIST_LENGTH)

/*
uint16_t test_lists[LIST_COUNT][LIST_LENGTH] = { 
{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19}, 
{6, 14, 22, 3, 7, 24, 16, 20, 8, 12, 23, 11, 9, 13, 1, 15, 21, 17, 18, 19},
{6, 21, 22, 12, 9, 24, 25, 20, 7, 19, 26, 11, 29, 28, 1, 15, 14, 27, 18, 3}
};
*/

void file_write(char* filename, void *data, size_t size) {
  FILE *file;
  file = fopen(filename, "wb");
  fwrite(data, 1, size, file);
  fclose(file);
}

// generates a mock slst
entry *test() {
  entry *entry;
  slst *slst_item;
  size_t item_size;
  eid_t eid;
  poly_id lists[LIST_COUNT][LIST_LENGTH];
  poly_id tmp;
  int i, j, k, l, m;
  void *entry_data;
  int pass;
  
  time_t t;
  srand((unsigned)time(&t));
  
  // create the mock poly_id lists
  for (j=0;j<LIST_LENGTH;j++) {
    lists[0][j].poly_idx = j;
    lists[0][j].world_idx = 0;
    lists[0][j].flag = 0;
  }
  m = LIST_LENGTH;
  for (i=1;i<LIST_COUNT;i++) {
    memcpy(&lists[i][0], &lists[i-1][0], LIST_SIZE);
    
    // randomly permute
    for (j=0;j<LIST_LENGTH/4;j++) {
      k = (rand() % LIST_LENGTH);
      l = (rand() % LIST_LENGTH);
      tmp = lists[i][k];
      lists[i][k] = lists[i][l];
      lists[i][l] = tmp;
    }
    
    // randomly replace
    for (j=0;j<LIST_LENGTH/4;j++) {
      k = (rand() % LIST_LENGTH);
      lists[i][k].poly_idx = m++;
    }
  }
  
  /*
  for (i=0;i<LIST_COUNT;i++) {
    for (j=0;j<LIST_LENGTH;j++) {
	  lists[i][j].poly_idx = test_lists[i][j];
	  lists[i][j].world_idx = 0;
	  lists[i][j].flag = 0;
	}
  }
  */
  
  // write lists to the console
  printf("poly_id lists:\n");
  for (i=0;i<LIST_COUNT;i++) {
    printf("list %i:\n", i+1);
    for (j=0;j<LIST_LENGTH;j++) {
      printf("%i ", poly_id_val(lists[i][j]));
    }
    printf("\n");
  }
  
  // create the SLST entry
  str_eid("e001S", &eid); 
  entry = entry_alloc(LIST_COUNT+1);
  entry_init(entry, eid, 4);
  
  // create the first/RAW poly id item
  item_size = sizeof(slst) + LIST_SIZE;
  slst_item = (slst*)malloc(item_size);
  slst_item->type = 0;
  slst_item->length = LIST_LENGTH;
  memcpy(&slst_item->poly_ids, &lists[0], LIST_SIZE);
  entry->items[0] = (uint8_t*)slst_item;
  entry->item_sizes[0] = item_size;
  
  // create the remaining items
  for (i=1;i<LIST_COUNT;i++) {
    slst_item = slst_encode(&lists[i-1], &lists[i], 
                            LIST_LENGTH, LIST_LENGTH, 
                            &item_size);
    entry->items[i] = (uint8_t*)slst_item;
    entry->item_sizes[i] = item_size;
  }
  
  // create the last/RAW poly id item
  item_size = sizeof(slst) + LIST_SIZE;
  slst_item = (slst*)malloc(item_size);
  slst_item->type = 0;
  slst_item->length = LIST_LENGTH;
  memcpy(&slst_item->poly_ids, &lists[LIST_COUNT-1], LIST_SIZE);
  entry->items[LIST_COUNT] = (uint8_t*)slst_item;
  entry->item_sizes[LIST_COUNT] = item_size;
  
  // verify that the unencoded lists can be reproduced by decoding
  slst_decode_forward(entry, 1, &lists[0], &lists[2], LIST_LENGTH, &m, 0);
  printf("decoded list 1:\n");
  for (j=0;j<LIST_LENGTH;j++) {
    printf("%i ", poly_id_val(lists[2][j]));
  }
  pass = 1;
  for (j=0;j<LIST_LENGTH;j++) {
    if (!poly_ids_eq(lists[2][j], lists[1][j])) {
	  pass = 0;
	  break;
    }
  }
  if (!pass)
    printf("FAILED\n");
  
  // return the entry
  return entry;
}
                
int main(int argc, char **argv) {
  char filename[11];
  void *data;
  entry *en_slst;
  size_t size;
  char str[6];
  
  en_slst = test();
  eid_str(&str, en_slst->eid);
  sprintf(&filename, "%s.slst", str);
  
  size = entry_size(en_slst);
  en_slst = entry_pack(en_slst, 1);
  data = entry_write(en_slst);
  file_write(filename, data, size);
  
  free(en_slst);
  
  return 0;
}       

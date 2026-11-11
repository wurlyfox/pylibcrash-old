#include <stdio.h>
#include <stdint.h>

#include "nsf.h"

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
	int i, ii;
	entry *entry;
	eid_t eid;
	char str[6];
	uint8_t *item;
	size_t item_size;
		
	str_eid("e009S", &eid);	
	entry = nsf_entry(nsf, eid);

	eid_str(&str, entry->eid);
	printf("eid: %s\n", str);
	for (i=0;i<entry->item_count;i++) {
		printf("item %i\n", i);
		item = entry->items[i];
		item_size = entry_item_size(entry, i);
		for (ii=0;ii<item_size;ii++) {
			if (!(ii%16)) { printf("\n"); }
			printf("%02x ", item[ii]);
		}
		printf("\n");
	}
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

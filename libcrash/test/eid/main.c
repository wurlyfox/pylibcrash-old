#include <stdio.h>
#include "entry.h"

		
int main(int argc, char **argv) {
	char *value;
	eid_t eid;
	char str[6];
	
	value = argv[1];
	sscanf(value, "%x", &eid);
	eid_str(str, eid);
	printf("%s\n", str);
	
	return 0;
}	

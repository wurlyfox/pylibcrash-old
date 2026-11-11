#ifndef TYPES_H
#define TYPES_H

#include <stdint.h>
#include <stddef.h>

typedef uint32_t unk32_t;

#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))

#define BITFIELDS_02(a01, a02) \
  a02; a01;
#define BITFIELDS_03(a01, a02, a03) \
  a03; a02; a01;
#define BITFIELDS_04(a01, a02, a03, a04) \
  a04; a03; a02; a01;
#define BITFIELDS_05(a01, a02, a03, a04, a05) \
  a05; a04; a03; a02; a01;
#define BITFIELDS_06(a01, a02, a03, a04, a05, a06) \
  a06; a05; a04; a03; a02; a01;
#define BITFIELDS_07(a01, a02, a03, a04, a05, a06, a07) \
  a07; a06; a05; a04; a03; a02; a01;
#define BITFIELDS_08(a01, a02, a03, a04, a05, a06, a07, a08) \
  a08; a07; a06; a05; a04; a03; a02; a01;
#define BITFIELDS_09(a01, a02, a03, a04, a05, a06, a07, a08, a09) \
  a09; a08; a07; a06; a05; a04; a03; a02; a01;
    
#endif

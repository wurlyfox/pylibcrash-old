#include "gfx.h"

void shader_blue(poly_id poly_id, fpoly poly, pnt32 point, 
                 uint8_t (*color)[4]) { 
  (*color)[0] = 255;
  (*color)[1] = 128;
  (*color)[2] = 128;					 
}

void shader_green(poly_id poly_id, fpoly poly, pnt32 point, 
                 uint8_t (*color)[4]) { 
  (*color)[0] = 128;
  (*color)[1] = 255;
  (*color)[2] = 128;					 
}

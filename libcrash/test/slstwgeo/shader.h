#ifndef SHADER_H
#define SHADER_H

#include "types.h"
#include "gfx.h"

extern void shader_blue(poly_id poly_id, fpoly poly, pnt32 point, 
                         uint8_t(*color)[4]); 
extern void shader_green(poly_id poly_id, fpoly poly, pnt32 point, 
                         uint8_t(*color)[4]);
                         
#endif

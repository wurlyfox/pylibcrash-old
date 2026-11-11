#ifndef GOOL_H
#define GOOL_H

#include "types.h"
#include "entry.h"

typedef struct {
  uint32_t type;
  uint32_t category;
  unk32_t unk_0x8;
  uint32_t init_fp;
  uint32_t subtype_map_idx;
  unk32_t unk_0x14;
} gool_header;

typedef struct {
  uint16_t event_map[0];
  uint16_t subtype_map[];
} gool_state_maps;

typedef struct {
  uint32_t flags;
  uint32_t status_c;
  uint16_t extern_idx;
  uint16_t pc_event;
  uint16_t pc_trans;
  uint16_t pc_code;
} gool_state;

#define gool_anim_header struct { \
  uint8_t type; \
  uint8_t unused; \
  uint8_t length; \
  uint8_t unused_2; \
}

typedef struct {
  gool_anim_header;
  eid_t eid;
} gool_vertex_anim;

typedef struct {
  gool_anim_header;
  eid_t tpage;
  uint32_t clut_texinfos[];
} gool_sprite_anim;

typedef struct {
  uint32_t clutinfo;
  uint32_t texinfo;
  uint16_t width;
  uint16_t height;
} gool_glyph;

typedef struct {
  gool_anim_header;
  eid_t tpage;
  gool_glyph glyphs[63];
  gool_frag_rect backdrop;
} gool_font;

typedef struct {
  gool_anim_header;
  unk32_t unk_0x4;
  uint32_t font_offset;
  char strings[];
} gool_text;

typedef struct {
  uint32_t clutinfo;
  uint32_t texinfo;
  uint16_t x1;
  uint16_t y1;
  uint16_t x2;
  uint16_t y2;
} gool_frag_rect;

typedef struct {
  gool_anim_header;
  eid_t tpage;
  uint32_t rect_count; /* per frame */
  gool_frag_rect rects[];
} gool_frag_anim;

typedef union {
  struct {
    gool_anim_header;
    uint8_t data[];
  };
  gool_vertex_anim v;
  gool_sprite_anim s;
  gool_font f;
  gool_text t;
  gool_frag_anim r;
} gool_anim;

#endif

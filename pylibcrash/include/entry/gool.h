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
} gool_state_map;
typedef struct {
  uint32_t flags;
  uint32_t status_c;
  uint16_t extern_idx;
  uint16_t pc_event;
  uint16_t pc_trans;
  uint16_t pc_code;
} gool_state;
typedef struct {
  uint8_t type;
  uint8_t unused;
  uint8_t length;
  uint8_t unused_2;
  uint8_t data[];
} gool_anim;
typedef struct {
  uint8_t type;
  uint8_t unused;
  uint8_t length;
  uint8_t unused_2;
  eid_t svtx;
} gool_vertex_anim;
typedef struct {
  uint8_t type;
  uint8_t unused;
  uint8_t length;
  uint8_t unused_2;
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
  uint8_t type;
  uint8_t unused;
  uint8_t length;
  uint8_t unused_2;
  eid_t tpage;
  gool_glyph glyphs[];
} gool_font;
typedef struct {
  uint8_t type;
  uint8_t unused;
  uint8_t length;
  uint8_t unused_2;
  unk32_t unk_0x4;
  uint32_t glyphs_offset;
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
  uint8_t type;
  uint8_t unused;
  uint8_t length;
  uint8_t unused_2;
  eid_t tpage;
  uint32_t rect_count;
  gool_frag_rect rects[];
} gool_frag_anim;

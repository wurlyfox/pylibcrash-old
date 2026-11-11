#ifndef ZONE_H
#define ZONE_H

#include "../gfx.h"
#include "types.h"
#include "entry.h"

typedef struct {
  union {
    eid_t eid;
    entry *entry;
    uint32_t key;
  };
  /*union { */
  uint32_t reserved[0xF];
  /*
  struct {
    vec32 trans; // 0x1
    wgeo_header *header; // 0x4
    wgeo_polygon *polygons; // 0x5
    wgeo_vertex *vertices; // 0x6
    wgeo_texinfo *texinfos; // 0x7
    entry *tpags[8]; // 0x8
  }
  */
} zone_world;

typedef struct {
  union {
    struct {
      mat16 light_mat;
      rgb16 color;
    };
    uint16_t l[12];
  };
  union {
    struct {
      mat16 color_mat;
      rgb16 intensity;
    };
    uint16_t c[12];
  };
} gool_colors;

/*
change for c1c:

typedef struct {
  uint32_t vram_fill_height;
  uint32_t unknown_a;
  uint32_t visibility_depth;
  uint32_t unknown_b;   
  uint32_t unknown_c;   
  uint32_t unknown_d;   
  uint32_t unknown_e;   
  uint32_t flags;       
  uint32_t death_y; 
  uint32_t unknown_f;
  uint32_t unknown_g;
  uint32_t unknown_h;
  uint8_t vram_fill_r;
  uint8_t vram_fill_g;
  uint8_t vram_fill_b;
  uint8_t unused_a;
  uint8_t far_color_r;
  uint8_t far_color_g;
  uint8_t far_color_b;
  uint8_t unused_b;
  gool_colors object_colors;
  gool_colors player_colors;
} zone_gfx;

typedef struct {
  uint32_t world_count;
  zone_world worlds[8];
  uint32_t paths_idx;
  uint32_t path_count;
  uint32_t entity_count;
  uint32_t neighbor_count;
  eid_t neighbor[8];
  uint32_t tpage_count;   
  uint32_t tchunk_count;  
  eid_t tpage[8];       
  uint32_t tchunk[32];    
  uint32_t game_flags;
  union {
    zone_gfx;
    zone_gfx gfx;
  };
} zone_header;

*/
typedef struct {
  uint32_t world_count;
  zone_world worlds[8];
  uint32_t paths_idx;
  uint32_t path_count;
  uint32_t entity_count;
  uint32_t neighbor_count;
  eid_t neighbor[8];
  uint32_t tpage_count;   
  uint32_t tchunk_count;  
  eid_t tpage[8];       
  uint32_t tchunk[32];    
  uint32_t game_flags;
  uint32_t vram_fill_height;
  uint32_t unknown_a;
  uint32_t visibility_depth;
  uint32_t unknown_b;
  uint32_t unknown_c;
  uint32_t unknown_d;
  uint32_t unknown_e;
  uint32_t flags;    
  uint32_t death_y; 
  uint32_t midi;
  uint32_t unknown_g;
  uint32_t unknown_h;
  uint8_t vram_fill_r;
  uint8_t vram_fill_g;
  uint8_t vram_fill_b;
  uint8_t unused_a;
  uint8_t far_color_r;
  uint8_t far_color_g;
  uint8_t far_color_b;
  uint8_t unused_b;
  /*
  uint16_t object_light_matrix[9];
  uint16_t object_back_color[3];
  uint16_t object_color_matrix[9];
  uint16_t object_back_color_intensity[3];
  uint16_t player_light_matrix[9];
  uint16_t player_back_color[3];
  uint16_t player_color_matrix[9];
  uint16_t player_back_color_intensity[3];
  */
  gool_colors object_colors;
  gool_colors player_colors;
} zone_header;

typedef struct {
  uint16_t root;
  uint16_t max_depth_x;
  uint16_t max_depth_y;
  uint16_t max_depth_z;
  uint16_t nodes[];
} zone_collisions;
  
typedef struct {
  int32_t x;
  int32_t y;
  int32_t z;
  uint32_t width;
  uint32_t height;
  uint32_t depth;
  uint32_t unknown;
  zone_collisions collisions;
} zone_dimensions;

typedef struct {
  uint8_t relation;
  uint8_t neighbor_zone_idx;
  uint8_t path_idx;
  uint8_t goal;
} zone_neighbor_path;

typedef struct {
  int16_t x;
  int16_t y;
  int16_t z;
  int16_t rot_x;
  int16_t rot_y;
  int16_t rot_z;
} zone_path_point;

typedef struct {
  eid_t slst;
  entry *parent_zone;
  uint32_t neighbor_path_count;
  zone_neighbor_path neighbor_paths[4]; /* 0xC, 0xD, 0xE, 0xF; 0x10, 0x11, 0x12, 0x13; 0x14, 0x15, 0x16, 0x17; 0x18, 0x19, 0x1A, 0x1B */
  uint8_t entrance_index;
  uint8_t exit_index;
  uint16_t length;
  uint16_t cam_mode;
  uint16_t avg_node_dist;
  uint16_t cam_zoom;
  uint16_t unknown_a;
  uint16_t unknown_b;
  uint16_t unknown_c;
  int16_t direction_x;
  int16_t direction_y;
  int16_t direction_z;
  zone_path_point points[];
} zone_path;

typedef struct {
  int16_t x;
  int16_t y;
  int16_t z;
} zone_entity_path_point;

typedef struct
{
  entity *parent_zone;
  uint16_t spawn_flags;
  uint16_t group;
  uint16_t id;
  uint16_t path_length;
  union {
    struct {
      uint16_t init_flags_a;
      uint16_t init_flags_b;
      uint16_t init_flags_c;
    }
    struct {
      ang16 y;
      ang16 x;
      ang16 z;
    } rot;
  };
  uint8_t type;
  uint8_t subtype;
  union {
    zone_entity_path_point path_points[];
    zone_entity_path_point loc;
  };
} zone_entity;

typedef struct {
  int32_t x;
  int32_t y;
  int32_t z;
  uint32_t width;
  uint32_t height;
  uint32_t depth;
} zone_bounds;

#endif

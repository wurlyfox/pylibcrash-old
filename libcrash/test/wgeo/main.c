#include <stdio.h>
#include <stdint.h>
#include <SDL/SDL.h>

#include "nsf.h"
#include "gfx.h"
#include "entry/zdat.h"

#define clamp(a,b,c) ((a)<(b)?b:(a)>(c)?c:a)

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

void ns_files_read(char *filename, nsd **p_nsd, nsf **p_nsf) {
  void *data;
  size_t size;
  nsf *nsf;
  nsd *nsd;
  
  data = file_read(filename, &size);
  nsd = nsd_read(data);
  filename[11] = 'F';
  data = file_read(filename, &size);
  nsf = nsf_read(data, nsd);
  
  *p_nsd = nsd;
  *p_nsf = nsf;
  
  return nsd;
}

void entry_find_type(nsf *nsf, int type, entry **entries, int *count) {
  int i, ii, c;
  nsd *nsd;
  page *page;
  entry *entry;
  
  c=0;
  nsd = nsf->dir;
  for (i=0;i<nsd->page_count;i++) {
    page = &nsd->pages[i];
    if (page->type == 1) continue;
    for (ii=0;ii<page->entry_count;ii++) {
      entry = page->entries[ii];
      if (entry->type != type) continue;
      entries[c++] = entry;
    }
  }
  *count = c;
}

#define VIEWPORT_W 320
#define VIEWPORT_H 200
#define VIEWPORT_PIXELS VIEWPORT_W*VIEWPORT_H*3

typedef struct {
  uint8_t pixels[VIEWPORT_PIXELS];
  entry *zone;
  int path_idx;
  int path_pt_idx;
  vec32 screen_offset;
  vec32 cam_trans;
  ang32 cam_rot;
  int poly_count;
  poly_id poly_ids[100000];
  fpoly polys[100000];
} gfx_context;

void gfx_context_init_offset(nsf *nsf, gfx_context *context) {
  nsd_ldat *ldat;
  uint16_t offset_z;
  
  ldat = nsd_ldat(nsf->dir);
  switch (ldat->screen_proj) {
  case 0x1E: offset_z = 0x3C0; break;
  case 0x25: offset_z = 0x320; break;
  case 0x37: offset_z = 0x1F4; break;
  case 0x3C: offset_z = 0x1CC; break;
  case 0x5A: offset_z = 0x120; break;
  }

  context->screen_offset.x = VIEWPORT_W/2;
  context->screen_offset.y = VIEWPORT_H/2;
  context->screen_offset.z = offset_z;
}

void gfx_context_init(nsf *nsf, gfx_context *context) {
  entry *zones[100];
  int zone_count, i, ii;
  zone_header *header;
  eid_t eid;
  
  
  // set the context zone to the one that contains the below world
  str_eid("s2_9W", &eid);
  entry_find_type(nsf, 7, &zones, &zone_count);
  
  context->zone = 0;
  for (i=0;i<zone_count;i++) {
    header = (zone_header*)(zones[i]->items[0]);
    for (ii=0;ii<header->world_count;ii++) {
      if (header->worlds[ii].wgeo == eid) {
        context->zone = zones[i];
        break;
      }
    }
    if (context->zone) break;
  }  
  context->path_idx = 0;
  context->path_pt_idx = 0;
  context->cam_rot.x = 0;
  context->cam_rot.y = 0;
  context->cam_rot.z = 0;
  context->cam_trans.x = 0;
  context->cam_trans.y = 0;
  context->cam_trans.z = 0;
  gfx_context_init_offset(nsf, context);
}

void gfx_context_update(nsf *nsf, gfx_context *context) {
  
  memset(context->pixels, 0, VIEWPORT_PIXELS);
  
  zdat_project(nsf, 
               context->zone, context->path_idx, context->path_pt_idx, 
               context->screen_offset,
               context->cam_trans, context->cam_rot, 
               context->poly_ids, &context->polys, &context->poly_count);
  draw_polys_wireframe(context->poly_ids, 
                       context->polys, context->poly_count, 
                       0, VIEWPORT_W, VIEWPORT_H, context->pixels);
  
}

void gfx_context_update_path(gfx_context *context, 
                             int path_idx, int path_pt_idx) {
  entry *zone;                             
  zone_header *header;
  zone_path *path;
  
  zone = context->zone;
  header = (zone_header*)zone->items[0];
  path = (zone_path*)zone->items[header->paths_idx+path_idx];
  
  // first change the current path to next or prev at boundaries
  // don't know the point in that path yet to adjust to 
  // (as the new path may be an invalid index and thus at zone 
  //  boundaries) 
  path_pt_idx = clamp(path_pt_idx, -1, path->length);
  if (path_pt_idx == -1)
    path_idx--;
  else if (path_pt_idx == path->length)
    path_idx++;
    
  // clamp the current path to first or last at zone boundaries
  // adjust to first point in first path, or last point in last path
  // (the -1 will force control to below where path pt is set to the 
  //  last point)  
  path_idx = clamp(path_idx, -1, header->path_count);
  if (path_idx == -1) {
    path_idx = 0;
    path_pt_idx = 0;
  }
  else if (path_idx == header->path_count) {
    path_idx = header->path_count-1;
    path_pt_idx = -1;
  }
  
  // finally reset the current path point if the path was changed
  if (path_pt_idx == path->length) {
    path_pt_idx = 0;
  }
  else if (path_pt_idx == -1) {
    path = (zone_path*)zone->items[header->paths_idx+path_idx];
    path_pt_idx = path->length-1;
  }
  
  context->path_idx = path_idx;
  context->path_pt_idx = path_pt_idx;
}
    
int main(int argc, char **argv) {
  char *filename;
  nsf *nsf;
  nsd *nsd;
  gfx_context context;
  SDL_Surface *screen, *draw;
  SDL_Event event;
  int keys[256];
  int path_idx, path_pt_idx;

  filename = argv[1];
  
  ns_files_read(filename, &nsd, &nsf);
  gfx_context_init(nsf, &context);  
    
  SDL_Init(SDL_INIT_EVERYTHING);
  screen = SDL_SetVideoMode(VIEWPORT_W, VIEWPORT_H, 24, SDL_SWSURFACE);
  draw = SDL_CreateRGBSurfaceFrom(
    (void*)context.pixels, 
    VIEWPORT_W, VIEWPORT_H, 24, VIEWPORT_W*3, 
    0xFF0000, 0x00FF00, 0x0000FF, 0x0
  );
  
  while(1) {
    while(SDL_PollEvent(&event)) {            
      switch(event.type) {
      case SDL_KEYDOWN:
        keys[event.key.keysym.sym] = 1;
        break;
      case SDL_KEYUP:
        keys[event.key.keysym.sym] = 0;
        break;  
      default:
        break;
      }
    }
    if (keys[SDLK_ESCAPE]) break;
    
    path_idx = context.path_idx;
    path_pt_idx = context.path_pt_idx;
    if (keys['a']) {
      gfx_context_update_path(&context, path_idx, path_pt_idx+1);
    }
    if (keys['z']) {
      gfx_context_update_path(&context, path_idx, path_pt_idx-1);
    }
    if (keys['s']) {
      gfx_context_update_path(&context, path_idx+1, 0);
    }
    if (keys['x']) {
      gfx_context_update_path(&context, path_idx-1, 0);
    }
    
    gfx_context_update(nsf, &context);
    memcpy((void*)screen->pixels, (void*)context.pixels, VIEWPORT_PIXELS);
    SDL_BlitSurface(draw, 0, screen, 0);
    SDL_Flip(screen); 
  } 

  SDL_FreeSurface(draw);
  SDL_FreeSurface(screen);
  free(nsf);
  free(nsd);
  
  return 0;
} 

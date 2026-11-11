#include <stdio.h>
#include <stdint.h>
#include <SDL/SDL.h>

#include "nsf.h"
#include "gfx.h"
#include "entry/zdat.h"

#include "scene.h"
#include "shader.h"

#define wrap(x,a,b) ((x)>=(a)?(x)<=(b)?(x):(a):(b))

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
#define VIEWPORT_H 224
#define VIEWPORT_PIXELS VIEWPORT_W*VIEWPORT_H*3

typedef struct {
  scene scene;
  uint8_t pixels[VIEWPORT_PIXELS];
  int draw_mode;
} gfx_context;

void gfx_context_init(nsf *nsf, gfx_context *context) {
  entry *zones[100];
  int zone_count, i, ii;
  zone_header *header;
  eid_t eid;
  entry *zone;
  
  // set the context zone to the one that contains the below world
  str_eid("1__9W", &eid);
  entry_find_type(nsf, 7, &zones, &zone_count);
  
  zone = 0;
  for (i=0;i<zone_count;i++) {
    header = (zone_header*)(zones[i]->items[0]);
    for (ii=0;ii<header->world_count;ii++) {
      if (header->worlds[ii].wgeo == eid) {
        zone = zones[i];
        break;
      }
    }
    if (zone) break;
  }
  
  // scene only has 1 zone for now
  scene_init(nsf, &context->scene, zone, VIEWPORT_W, VIEWPORT_H);    

  context->draw_mode = 0;
}

void gfx_context_update(nsf *nsf, gfx_context *context) {
  scene *scene;
  scene = &context->scene;
  
  memset(&context->pixels, 0, VIEWPORT_PIXELS);
  scene_project(nsf, scene);
  //draw_polys_wireframe(scene->poly_ids, 
  //                     scene->polys, scene->poly_count, 
  //                     0, VIEWPORT_W, VIEWPORT_H, context->pixels);
  //draw_polys(scene->poly_ids, 
  //           scene->polys, scene->poly_count,
  //           VIEWPORT_W, VIEWPORT_H, 
  //           context->pixels);
}

/**
 * attempts to compute the poly ids which exist in the current sort list
 * based on a z-buffer test of the actual projected world polygons
 * 
 * then draws the scene with additional polys representing the error 
 * difference in the just computed and already existing pre-computed 
 * sort list
 */ 
void gfx_context_update_diffs(nsf *nsf, gfx_context *context) {
  scene *_scene, *diff_a, *diff_b;
  scene *scene_shaded;
  
  gfx_context_update(nsf, context);
  
  _scene = malloc(sizeof(scene));
  scene_init(nsf, _scene, context->scene.zone, VIEWPORT_W, VIEWPORT_H);
  _scene->path_idx = context->scene.path_idx;
  _scene->path_pt_idx = context->scene.path_pt_idx;
  scene_compute_polys(nsf, _scene, VIEWPORT_W, VIEWPORT_H);
  scene_project(nsf,_scene); // reproject
  
  diff_a = scene_difference(nsf, &context->scene, _scene);
  diff_b = scene_difference(nsf, _scene, &context->scene);
  diff_b->path_idx = context->scene.path_idx;
  diff_b->path_pt_idx = context->scene.path_pt_idx;
  
  switch (context->draw_mode) {
  case 0:
    scene_shaded = _scene;
    break;
  case 1:
    scene_shaded = &context->scene;
    break;
  case 2:
    scene_shaded = diff_a;
    break;
  case 3:
    scene_shaded = diff_b;
    break;
  default:
    scene_shaded = &context->scene;
    break;
  }
  
  draw_polys(scene_shaded->poly_ids, 
             scene_shaded->polys, scene_shaded->poly_count,
             VIEWPORT_W, VIEWPORT_H, 
             context->pixels);
  /*
  draw_polys_wireframe(scene_shaded->poly_ids, 
                       scene_shaded->polys, scene_shaded->poly_count,
                       0, VIEWPORT_W, VIEWPORT_H, 
                       context->pixels);
  */
  if (context->draw_mode < 2) {          
  draw_polys_wireframe(diff_a->poly_ids, 
                       diff_a->polys, diff_a->poly_count,
                       shader_blue, VIEWPORT_W, VIEWPORT_H, 
                       context->pixels);
  draw_polys_wireframe(diff_b->poly_ids, 
                       diff_b->polys, diff_b->poly_count,
                       shader_green, VIEWPORT_W, VIEWPORT_H, 
                       context->pixels);                       
  }

  
  free(_scene);
  free(diff_a);
  free(diff_b);
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
    
    path_idx = context.scene.path_idx;
    path_pt_idx = context.scene.path_pt_idx;
    if (keys['a']) {
      scene_update_path(nsf, &context.scene, path_idx, path_pt_idx+1);
    }
    if (keys['z']) {
      scene_update_path(nsf, &context.scene, path_idx, path_pt_idx-1);
    }
    if (keys['s']) {
      scene_update_path(nsf, &context.scene, path_idx+1, 0);
    }
    if (keys['x']) {
      scene_update_path(nsf, &context.scene, path_idx-1, 0);
    }
    if (keys['t']) {
      slst_wgeo_stats(nsf, &context.scene, VIEWPORT_W, VIEWPORT_H);
    }
    if (keys['m']) {
      context.draw_mode = wrap(context.draw_mode+1,0,3);
    }
    if (keys['d']) {
      context.scene.screen_offset.z = wrap(context.scene.screen_offset.z+1,20,0x800);
    }
    if (keys['c']) {
      context.scene.screen_offset.z = wrap(context.scene.screen_offset.z-1,20,0x800);
    }
    
    // gfx_context_update(nsf, &context);
    gfx_context_update_diffs(nsf, &context);
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

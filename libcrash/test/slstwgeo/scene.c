#include "scene.h"
#include "entry/zdat.h"
#include "entry/wgeo.h"
#include "entry/slst.h"

#include "rasterize.h"
#include "stats.h"

#define clamp(a,b,c) ((a)<(b)?b:(a)>(c)?c:a)

/** 
 * sets the initial screen offset vector for a scene
 * (the z offset is determined from a per-level value set in the nsd) 
 */ 
static void scene_init_offset(nsf *nsf, scene *scene, int w, int h) {
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

  scene->screen_offset.x = w/2;
  scene->screen_offset.y = h/2;
  scene->screen_offset.z = offset_z;
}

/** 
 * sets the initial zone, path, and path point for a scene
 * also loads the list of poly ids for that point 
 */ 
static void scene_init_path(nsf *nsf, scene *scene, entry *zone, 
                           int path_idx, int path_pt_idx) {
  scene->zone = zone;
  scene->path_idx = path_idx;
  scene->path_pt_idx = path_pt_idx;
  scene_update_poly_ids(nsf, scene, path_idx, path_pt_idx, 1);
}

/**
 * initializes a scene with the initial zone and viewport dimensions
 *
 */ 
void scene_init(nsf *nsf, scene *scene, entry *zone, int w, int h) {
  scene->cam_rot.x = 0;
  scene->cam_rot.y = 0;
  scene->cam_rot.z = 0;
  scene->cam_trans.x = 0;
  scene->cam_trans.y = 0;
  scene->cam_trans.z = 0;
  scene->deltas_enabled = 1;
  scene_init_offset(nsf, scene, w, h);
  scene_init_path(nsf, scene, zone, 0, 0);
}

/**
 * updates the list of poly ids in a scene to the list for the given
 * path and path point
 * 
 * the path and path point index must be valid. behavior is undefined
 * if the indices are invalid.
 */
poly_id poly_id_buf[100000];
void scene_update_poly_ids(nsf *nsf, scene *scene,
                           int path_idx, int path_pt_idx, int force) {
  int i, poly_count;
  slst *raw;
  entry *zone, *slst;
  zone_header *header;
  zone_path *path;
  
  zone = scene->zone;
  header = (zone_header*)zone->items[0];
  path = (zone_path*)zone->items[header->paths_idx+path_idx];
  slst = nsf_entry(nsf, path->slst);
  if ((path_idx != scene->path_idx) || force) {
    if (path_idx < path->length/2) {
      raw = slst->items[0];
      memcpy(&scene->poly_ids,raw->poly_ids,raw->length*sizeof(poly_id));
      scene->poly_count = raw->length;
      scene->path_pt_idx = 0;
    }
    else {
      raw = slst->items[path->length-1];
      memcpy(&scene->poly_ids,raw->poly_ids,raw->length*sizeof(poly_id));
      scene->poly_count = raw->length;
      scene->path_pt_idx = path->length-1;
    }
  }
  if (path_pt_idx > scene->path_pt_idx) {
    for (i=scene->path_pt_idx;i<path_pt_idx;i++) {
      slst_decode_forward(slst, i+1, scene->poly_ids, &poly_id_buf, 
                           scene->poly_count, &poly_count, 0);
      memcpy(&scene->poly_ids,&poly_id_buf,poly_count*sizeof(poly_id));
      scene->poly_count = poly_count;
    }
  }
  else if (path_pt_idx < scene->path_pt_idx) {
    for (i=scene->path_pt_idx;i>path_pt_idx;i--) {
      slst_decode_backward(slst, i, scene->poly_ids, &poly_id_buf,
                           scene->poly_count, &poly_count, 0);
      memcpy(&scene->poly_ids,&poly_id_buf,poly_count*sizeof(poly_id));
      scene->poly_count = poly_count;
    }
  }
  scene->path_idx = path_idx;
  scene->path_pt_idx = path_pt_idx;
}

/**
 * updates the current path and path point for a scene. 
 * 
 * the path is adjusted to the next path in the current zone if the path 
 * point index exceeds the path length (minus one). the path is adjusted
 * to the previous path in the zone if the point index is less than zero. 
 * 
 * the path index is clamped between zero and the number of paths in the
 * current zone (minus one).
 * 
 * also updates the list of poly ids in the scene accordingly.
 */
void scene_update_path(nsf *nsf, scene *scene, 
                       int path_idx, int path_pt_idx) {
  entry *zone;                             
  zone_header *header;
  zone_path *path;
  
  zone = scene->zone;
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
  
  if (scene->deltas_enabled)
    scene_update_poly_ids(nsf, scene, path_idx, path_pt_idx, 0);
  scene->path_idx = path_idx;
  scene->path_pt_idx = path_pt_idx;
}

// char zdat_stats[100000];
void scene_project(nsf *nsf, scene *scene) {  
  // replace scene->poly_ids with 0 to disable the poly ids/slst
  zdat_project(nsf, 
               scene->zone, scene->path_idx, scene->path_pt_idx, 
               scene->screen_offset,
               scene->cam_trans, scene->cam_rot, 
               0,
               &scene->poly_ids, &scene->polys, &scene->poly_count);
   /*
   zdat_project_stats(nsf, 
               scene->zone, scene->path_idx, scene->path_pt_idx, 
               scene->screen_offset,
               scene->cam_trans, scene->cam_rot, 
               &scene->poly_ids, &scene->polys, &scene->poly_count,
               &zdat_stats);
   printf(zdat_stats);
   */
}

void scene_all_poly_ids(nsf *nsf, scene *scene) {
  int i, ii;
  entry *zone, *world;
  zone_header *header_z;
  wgeo_header *header_w;
  poly_id *poly_id;
  
  zone = scene->zone;
  header_z = (zone_header*)zone->items[0];
  
  scene->poly_count = 0;
  poly_id = &scene->poly_ids;
  for (i=0;i<header_z->world_count;i++) {
    world = nsf_entry(nsf, header_z->worlds[i].wgeo);
    header_w = (wgeo_header*)world->items[0];
    for (ii=0;ii<header_w->poly_count;ii++,poly_id++) {
	    poly_id->world_idx = i;
	    poly_id->poly_idx = ii;
    }
	  scene->poly_count += header_w->poly_count;
  } 
  scene->deltas_enabled = 0; // do not update poly id list on update
}

fpoly *sort_polys;
int sort_poly_idxs(int *a, int *b) {
  float z_avg_a, z_avg_b;
  fpoly *poly_a, *poly_b;
  
  poly_a = &sort_polys[*a];
  poly_b = &sort_polys[*b];
  
  z_avg_a = poly_a->verts[0].z + poly_a->verts[1].z + poly_a->verts[2].z;
  z_avg_b = poly_b->verts[0].z + poly_b->verts[1].z + poly_b->verts[2].z;
  
  if (z_avg_a < z_avg_b) return 1;
  if (z_avg_b < z_avg_a) return -1;
  return 0;
}

void scene_sort_polys(nsf *nsf, scene *scene) {
  int i;
  int *poly_idxs;
  poly_id *poly_ids;
  fpoly *polys;
  
  poly_idxs = (int*)malloc(scene->poly_count*sizeof(int));
  poly_ids = (poly_id*)malloc(scene->poly_count*sizeof(poly_id));
  polys = (fpoly*)malloc(scene->poly_count*sizeof(fpoly));
  for (i=0;i<scene->poly_count;i++)
    poly_idxs[i] = i;
  
  sort_polys = &scene->polys;
  qsort(poly_idxs, scene->poly_count, sizeof(int), sort_poly_idxs);
  
  for (i=0;i<scene->poly_count;i++) {
    polys[i] = scene->polys[poly_idxs[i]];
    poly_ids[i] = scene->poly_ids[poly_idxs[i]];
  }  
  
  memcpy(&scene->polys, polys, scene->poly_count*sizeof(fpoly));
  memcpy(&scene->poly_ids, poly_ids, scene->poly_count*sizeof(poly_id));
  
  free(polys);
  free(poly_ids);
  free(poly_idxs);
}


void scene_compute_visible_polys(nsf *nsf, scene *scene, int w, int h) {
  int i, ii;
  z_struct *z_buf;
  int z_buf_len;
  poly_id *poly_ids;
  fpoly *polys;
  poly_id poly_id;
  fpoly poly;
  int poly_count;
  int *draw_count_map;
  
  z_buf_len = w*h;
  z_buf = (z_struct*)calloc(z_buf_len,sizeof(z_struct));
  draw_count_map = (int*)calloc(0x8000,sizeof(int));
  poly_ids = malloc(100000*sizeof(poly_id));
  polys = (fpoly*)malloc(100000*sizeof(fpoly));
  
  scene_all_poly_ids(nsf, scene);
  scene_project(nsf, scene);
  draw_polys_zbuf(scene->poly_ids, scene->polys, scene->poly_count, 
                  w, h, z_buf);
    
  poly_count = 0;
  for (i=0;i<z_buf_len;i++) {
    if (!z_buf[i].draw_count) continue;
    poly_id = z_buf[i].poly_id;
    if (draw_count_map[*(uint16_t*)&poly_id]++ < 1) continue;
    for (ii=0;ii<poly_count;ii++) {
	  if (poly_ids_eq(poly_ids[ii], poly_id)) break;
    }
    if (ii==poly_count) {
	  for (ii=0;ii<scene->poly_count;ii++) {
	    if (poly_ids_eq(scene->poly_ids[ii], poly_id)) break;
	  }
	  polys[poly_count] = scene->polys[ii];
      poly_ids[poly_count++] = poly_id;
    }
  }

  memcpy(&scene->poly_ids, poly_ids, poly_count*sizeof(poly_id));
  memcpy(&scene->polys, polys, poly_count*sizeof(fpoly));
  free(polys);
  free(poly_ids);
  free(draw_count_map);
  free(z_buf);
  
  scene->poly_count = poly_count;
  scene_sort_polys(nsf, scene);
}

void scene_compute_polys(nsf *nsf, scene *_scene, int w, int h) {
  int i;
  scene *prev, *next;
  scene *diff, *sect;
  scene *diff_p, *diff_n;
  
  prev = (scene*)malloc(sizeof(scene));
  next = (scene*)malloc(sizeof(scene));
  memcpy(prev, _scene, sizeof(scene)-offsetof(scene, poly_ids));
  memcpy(next, _scene, sizeof(scene)-offsetof(scene, poly_ids));
  scene_update_path(nsf, prev, prev->path_idx, prev->path_pt_idx-1);
  scene_update_path(nsf, next, next->path_idx, next->path_pt_idx+1);
  
  // if in prev and next but not in cur then keep
  // if not in prev and not in next then remove
  scene_compute_visible_polys(nsf, _scene, w, h);
  scene_compute_visible_polys(nsf, prev, w, h);
  scene_compute_visible_polys(nsf, next, w, h);
  
  sect = scene_intersection(nsf, prev, next);
  diff = scene_difference(nsf, sect, _scene);
  for (i=0;i<diff->poly_count;i++) {
    _scene->poly_ids[_scene->poly_count] = diff->poly_ids[i];
    _scene->polys[_scene->poly_count++] = diff->polys[i];
  }
  free(diff);
  free(sect);
  diff_p = scene_difference(nsf, _scene, prev); 
  diff_n = scene_difference(nsf, _scene, next); 
  sect = scene_intersection(nsf, diff_p, diff_n);
  diff = scene_difference(nsf, _scene, sect);
  
  memcpy(_scene, diff, sizeof(scene));
  free(diff);
  free(sect);
  free(diff_n);
  free(diff_p);
  free(next);
  free(prev);
  
  scene_sort_polys(nsf, _scene);
}

/**
 *  NOTE: self-allocating. need to free returned data.
 *
 */
 
/*
scene *scene_difference(nsf *nsf, scene *scene_a, scene *scene_b) {
  int i, ii;
  scene *diff;
  poly_id poly_id;
  
  if (scene_a->zone != scene_b->zone)
    return 0;
  
  diff = (scene*)malloc(sizeof(scene));
  memcpy(diff, scene_a, sizeof(scene)-offsetof(scene,poly_ids));
  diff->deltas_enabled = 0;
  diff->poly_count=0;  
  for(i=0;i<scene_a->poly_count;i++) {
    poly_id = scene_a->poly_ids[i];
    for(ii=0;ii<scene_b->poly_count;ii++) {
      if (poly_ids_eq(scene_b->poly_ids[ii],poly_id)) break;
    }
    if (ii==scene_b->poly_count) {
      diff->polys[diff->poly_count] = scene_a->polys[i];
      diff->poly_ids[diff->poly_count++] = poly_id;
    }
  }
  return diff;
}

scene *scene_intersection(nsf *nsf, scene *scene_a, scene *scene_b) {
  int i, ii;
  scene *sect;
  poly_id poly_id;
  
  if (scene_a->zone != scene_b->zone)
    return 0;
  
  sect = (scene*)malloc(sizeof(scene));
  memcpy(sect, scene_a, sizeof(scene)-offsetof(scene,poly_ids));
  sect->deltas_enabled = 0;
  sect->poly_count=0;  
  for(i=0;i<scene_a->poly_count;i++) {
    poly_id = scene_a->poly_ids[i];
    for(ii=0;ii<scene_b->poly_count;ii++) {
      if (poly_ids_eq(scene_b->poly_ids[ii],poly_id)) break;
    }
    if (ii!=scene_b->poly_count) {
      sect->polys[sect->poly_count] = scene_a->polys[i];
      sect->poly_ids[sect->poly_count++] = poly_id;
    }
  }
  return sect;
}
*/

scene *scene_difference(nsf *nsf, scene *scene_a, scene *scene_b) {
  int i, ii;
  scene *diff;
  poly_id poly_id;
  int *poly_id_map;
  
  if (scene_a->zone != scene_b->zone)
    return 0;
  
  poly_id_map = (int*)calloc(0x8000,sizeof(int));  
  diff = (scene*)malloc(sizeof(scene));
  memcpy(diff, scene_a, sizeof(scene)-offsetof(scene,poly_ids));
  diff->deltas_enabled = 0;
  diff->poly_count=0;  

  for (i=0;i<scene_b->poly_count;i++) {
    poly_id = scene_b->poly_ids[i];
    poly_id_map[poly_id_val(poly_id)] = 1;
  }
  for (i=0;i<scene_a->poly_count;i++) {
	poly_id = scene_a->poly_ids[i];
	if (!poly_id_map[poly_id_val(poly_id)]) {
	  diff->polys[diff->poly_count] = scene_a->polys[i];
	  diff->poly_ids[diff->poly_count++] = poly_id;
	}
  }
  free(poly_id_map);
  return diff;
}

scene *scene_intersection(nsf *nsf, scene *scene_a, scene *scene_b) {
  int i, ii;
  scene *sect;
  poly_id poly_id;
  int *poly_id_map;
  
  if (scene_a->zone != scene_b->zone)
    return 0;
  
  poly_id_map = (int*)calloc(0x8000,sizeof(int));  
  sect = (scene*)malloc(sizeof(scene));
  memcpy(sect, scene_a, sizeof(scene)-offsetof(scene,poly_ids));
  sect->deltas_enabled = 0;
  sect->poly_count=0;  

  for (i=0;i<scene_b->poly_count;i++) {
    poly_id = scene_b->poly_ids[i];
    poly_id_map[poly_id_val(poly_id)] = 1;
  }
  for (i=0;i<scene_a->poly_count;i++) {
	poly_id = scene_a->poly_ids[i];
	if (poly_id_map[poly_id_val(poly_id)]) {
	  sect->polys[sect->poly_count] = scene_a->polys[i];
	  sect->poly_ids[sect->poly_count++] = poly_id;
	}
  }
  free(poly_id_map);
  return sect;
}

void scene_differences(nsf *nsf, scene *scene_a, scene *scene_b) {
  scene *diff_a, *diff_b;

  if (scene_a->zone != scene_b->zone)
    return;
   
  diff_a = scene_difference(nsf, scene_a, scene_b);
  diff_b = scene_difference(nsf, scene_b, scene_a);
  
  memcpy(scene_a, diff_a, sizeof(scene));
  memcpy(scene_b, diff_b, sizeof(scene));
  
  free(diff_a);
  free(diff_b);
}

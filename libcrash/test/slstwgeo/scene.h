#ifndef SCENE_H
#define SCENE_H

#include "entry.h"
#include "gfx.h"

typedef struct {
  entry *zone;
  int path_idx;
  int path_pt_idx;
  vec32 screen_offset;
  vec32 cam_trans;
  ang32 cam_rot;
  int poly_count;
  poly_id poly_ids[100000];
  fpoly polys[100000];
  int deltas_enabled; // auto-update poly ids in scene_update_path
} scene;

extern void scene_init(nsf *nsf, scene *scene, entry *zone, 
                       int w, int h); 
extern void scene_update_poly_ids(nsf *nsf, scene *scene,
                                  int path_idx, int path_pt_idx, 
                                  int force);
extern void scene_update_path(nsf *nsf, scene *scene, 
                              int path_idx, int path_pt_idx);
extern void scene_project(nsf *nsf, scene *scene);


// extension functions
extern void scene_all_poly_ids(nsf *nsf, scene *scene);
extern void scene_compute_polys(nsf *nsf, scene *scene, 
                                int w, int h);
extern void scene_compute_visible_polys(nsf *nsf, scene *scene, 
                                        int w, int h);
extern scene *scene_difference(nsf *nsf, 
                              scene *scene_a, scene *scene_b);
extern scene *scene_intersection(nsf *nsf,
                                 scene *scene_a, scene *scene_b);
extern void scene_differences(nsf *nsf, 
                              scene *scene_a, scene *scene_b);
#endif

#ifndef STATS_H
#define STATS_H

#include "nsf.h"
#include "scene.h"

extern void slst_wgeo_stats(nsf *nsf, scene *src, int w, int h);

extern void wgeo_project_stats(entry *world, 
                        vec32 cam_trans, int16_t ms_cam_rot[3][3], 
                        vec32 screen_offset,
                        poly_id *poly_ids, fpoly *polys, int *poly_count,
                        char *stats);                        
extern void zdat_project_stats(nsf *nsf, entry *zone, 
                       int path_idx, int path_pt_idx, 
                       vec32 screen_offset, vec32 cam_trans, ang32 cam_rot,
                       poly_id *poly_ids, fpoly *polys, int *poly_count,
                       char *stats);

#endif

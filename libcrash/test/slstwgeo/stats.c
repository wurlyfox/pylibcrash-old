#include "stats.h"
#include "entry/zdat.h"
#include "entry/wgeo.h"
#include "misc/slst_stats.h"

static int scene_poly_idx(nsf *nsf, scene *scene, poly_id poly_id) {
  
  // we have a list of the corresponding poly ids for polys in the 
  // scene; for now the list will be the same at every path point
  // as sorting and clipping are disabled. this means that we can 
  // calculate poly index from the poly id.
  
  // edit: currently this will no longer work as sorting has been enabled
  
  int i, idx;
  entry *world;
  zone_header *header_z;
  wgeo_header *header_w;
  header_z = (zone_header*)(scene->zone->items[0]);
  idx = 0;
  for (i=0;i<header_z->world_count;i++) {
    if (i == poly_id.world_idx) break;
    world = nsf_entry(nsf, header_z->worlds[i].wgeo);
    header_w = (wgeo_header*)world->items[0];
    idx += header_w->poly_count; 
  }
  idx += poly_id.poly_idx;
  return idx;
}

scene before, after;
uint32_t stats_buf[100000];

void slst_wgeo_stats(nsf *nsf, scene *src, int w, int h) {
  int i, ii;
  char buf[100], l[3], r[3];
  slst_stats_node *node, *end;
  
  zone_header *header;
  zone_path *path;
  slst *raw;
  entry *slst;
  slst_stats *stats;
  int row, idx, zavg;
  
  // create scenes for holding the before and after poly id lists and
  // projected polygons
  scene_init(nsf, &before, src->zone, w, h);
  scene_init(nsf, &after, src->zone, w, h);
  
  scene_update_path(nsf, &before, src->path_idx, src->path_pt_idx);
  scene_update_path(nsf, &after, src->path_idx, src->path_pt_idx+1);

  if (before.path_idx != after.path_idx || 
      before.path_pt_idx != after.path_pt_idx-1)
    return;
    
  // project polygons in both scenes
  scene_project(nsf, &before);
  scene_project(nsf, &after);
  
  header = (zone_header*)(before.zone->items[0]);
  path = (zone_path*)before.zone->items[header->paths_idx+before.path_idx];
  slst = nsf_entry(nsf, path->slst);
  
  // regenerate the current poly id list at the before path pt using the 
  // slsts
  
  /*
  raw = slst->items[0];
  memcpy(&before.poly_ids, raw->poly_ids, raw->length*sizeof(poly_id));
  before.poly_count = raw->length;
  for (i=0;i<before.path_pt_idx;i++) {
    slst_decode_forward(slst, i+1, &before.poly_ids, &after.poly_ids, 
                        before.poly_count, &after.poly_count, 0);
    memcpy(&before.poly_ids, &after.poly_ids, 
           after.poly_count*sizeof(poly_id));
    before.poly_count = after.poly_count;
  }
  */
  
  // generate stats for from before path pt to after path pt
  stats = (slst_stats*)stats_buf;
  slst_stats_summary(slst, before.path_pt_idx, 
                     &before.poly_ids, &after.poly_ids, 
                     before.poly_count, &after.poly_count, 
                     stats);
  
  // render the stats poly ids with their corresponding projected poly 
  // vertex average z values at before and after path pts
  row = 0;
  for (i=0;i<stats->stage_count;i++) {
    printf("stats stage %i\n\n", i);
    if (i==stats->stage_count-1)
      end = &stats->nodes[stats->node_count];
    else
      end = stats->stages[i+1];
    for (node=stats->stages[i],ii=0;node!=end;node++,ii++) {
      strcpy(l, "  ");
      strcpy(r, "  ");
      if (node->type == 4) {
        slst_stats_swap_id(buf, node->i);
        l[0] = buf[0]; l[1] = '|'; // l[2] = '\0';
        r[0] = '|'; r[1] = buf[1]; // r[2] = '\9';
      }
      if (node->is_head) {
        if (node->type == 1) { strcpy(l, "+|"); }
        else if (node->type == 2) { strcpy(l, "-|"); }
        else if (node->type == 3) { strcpy(l, " |"); }
      }
      if (node->is_tail) {
        if (node->type == 1) { strcpy(r, "|+"); }
        else if (node->type == 2) { strcpy(r, "|-"); }
        else if (node->type == 3) { strcpy(r, "| "); }
      }
      if (row == 0)
        sprintf(buf, "%s%04x%s", l, *(uint16_t*)&node->poly_id, r);
      else if (row == 1) {
        idx = scene_poly_idx(nsf, &before, node->poly_id);
        zavg = (int)((before.polys[idx].verts[0].z
                    + before.polys[idx].verts[1].z
                    + before.polys[idx].verts[2].z)/3);
        sprintf(buf, " %06x ", zavg);
      }
      else if (row == 2) {
        idx = scene_poly_idx(nsf, &after, node->poly_id);
        zavg = (int)((after.polys[idx].verts[0].z
                    + after.polys[idx].verts[1].z
                    + after.polys[idx].verts[2].z)/3);
        sprintf(buf, " %06x ", zavg);
      }
      printf(buf);
      if ((ii%16)==15) {
        printf("\n");
        if (++row == 3) { row=0; }
        else { ii -= 16; node -= 16; }
      }
      else if ((node+1) == end) {
        printf("\n");
        if (++row == 3) { row=0; }
        else { ii -= (ii%16); node -= (ii%16); }
      }
    }
    printf("\n\n");
  }
}

  
#define cat_vec(vec) \
  sprintf(buf, #vec ": <%X, %X, %X>\n", vec.x, vec.y, vec.z); \
  strcat(stats, buf);
#define cat_vec_ind(vec,ind) \
  sprintf(buf, "%*s" #vec ": <%X, %X, %X>\n", ind, " ", \
    (int16_t)(vec.x), (int16_t)(vec.y), (int16_t)(vec.z)); \
  strcat(stats, buf) 
#define cat_mat(mat) \
  sprintf(buf, #mat ": [%4X, %4X, %4X]\n", \
    mat[0][0], mat[0][1], mat[0][2]); \
  strcat(stats, buf); \
  sprintf(buf, "%*s [%4X, %4X, %4X]\n", (int)strlen(#mat), " ", \
    mat[1][0], mat[1][1], mat[1][2]); \
  strcat(stats, buf); \
  sprintf(buf, "%*s [%4X, %4X, %4X]\n", (int)strlen(#mat), " ", \
    mat[2][0], mat[2][1], mat[2][2]); \
  strcat(stats, buf); 
#define cat_str_0(str) \
  strcat(stats, str);
#define cat_str_1(str,a1) \
  sprintf(buf, str, a1); \
  strcat(stats, buf);
#define cat_str_2(str,a1,a2) \
  sprintf(buf, str, a1, a2); \
  strcat(stats, buf);
#define cat_str_3(str,a1,a2,a3) \
  sprintf(buf, str, a1, a2, a3); \
  strcat(stats, buf);
  
void wgeo_project_stats(entry *world, 
                        vec32 cam_trans, int16_t ms_cam_rot[3][3], 
                        vec32 screen_offset,
                        poly_id *poly_ids, fpoly *polys, int *poly_count,
                        char *stats) {
  int i, ii, p;
  wgeo_header *header;
  wgeo_polygon *poly, *wpolys;
  wgeo_vertex *vert, *verts;
  pnt32 u_viewmodel, r_viewmodel, r_vert, u_vert;
  pnt16 v_vert;
  float v_vert_w;
  fpnt s_vert;
  uint32_t z13;
  int vert_idx[3];
  char str[6], buf[500];

  
  header = (wgeo_header*)world->items[0];
  //if (getWord(worldheader, 0x1C, true) == 1) { continue; }
  
  u_viewmodel.x = header->trans_x - (cam_trans.x >> 8);
  u_viewmodel.y = header->trans_y - (cam_trans.y >> 8);
  u_viewmodel.z = header->trans_z - (cam_trans.z >> 8);
  // cat_vec(u_viewmodel);
  
  // use camera rot matrix to transform ((model relative) unrotated 
  // view coords to (rotated model relative) view coords) 
  r_viewmodel = mat33_transform(ms_cam_rot, u_viewmodel);
  // cat_vec(r_viewmodel);
  
  wpolys = (wgeo_polygon*)world->items[1];
  verts = (wgeo_vertex*)world->items[2];
  
  if (!poly_ids) { *poly_count = header->poly_count; }
  for (i=0;i<*poly_count;i++) {
    cat_str_1("poly: %04X\n{\n", poly_ids ? *(uint16_t*)&poly_ids[i]: i);
    
    poly = poly_ids ? &wpolys[poly_ids[i].poly_idx] 
                    : &wpolys[i];
    vert_idx[0] = poly->a_idx;
    vert_idx[1] = poly->b_idx;
    vert_idx[2] = poly->c_idx;
 
    for (ii=0;ii<3;ii++) {
      vert = &verts[vert_idx[ii]];
      z13 = vert->z8+(vert->z2<<8)+(vert->z3<<10);
      
      u_vert.x = (int16_t)(vert->x << 3); // convert to 16 bit signed
      u_vert.y = (int16_t)(vert->y << 3); // before storing as 32 bit
      u_vert.z = (int16_t)(z13 << 3);     // signed
      
      // use cam rot mat to transform (model to rotated model coords)
      r_vert = mat33_transform(ms_cam_rot, u_vert);
      
      // offset rotated model relative view coords to yield view 
      // coords; [rot vert coords = rot model coords]
      v_vert.x = r_viewmodel.x + r_vert.x; // note the limiting to 16 bits, per the gte calculations
      v_vert.y = r_viewmodel.y + r_vert.y;
      v_vert.z = r_viewmodel.z + r_vert.z;
      cat_vec_ind(v_vert, 2);
      
      // project view to screen coords
      v_vert_w = (v_vert.z ? v_vert.z : 0.001f) / screen_offset.z;
      s_vert.x = screen_offset.x + ((float)v_vert.x / v_vert_w);
      s_vert.y = screen_offset.y + ((float)v_vert.y / v_vert_w);
      s_vert.z = v_vert.z; // no proj for z
      cat_vec_ind(s_vert, 2);
    
      polys[i].verts[ii] = s_vert;
      polys[i].vertws[ii] = v_vert_w;
    }
    cat_str_0("}\n");
  }
}

void zdat_project_stats(nsf *nsf, entry *zone, 
                       int path_idx, int path_pt_idx, 
                       vec32 screen_offset, vec32 cam_trans, ang32 cam_rot,
                       poly_id *poly_ids, fpoly *polys, int *poly_count,
                       char *stats) {
                    
  // get zone and path pt loc & rot;
  int i, ii;
  zone_header *header;
  zone_dimensions *dim;
  zone_path *path;
  zone_path_point* path_pt;
  int16_t m_cam_rot[3][3], ms_cam_rot[3][3];
  entry *world;
  int world_poly_count;
  poly_id poly_id;
  char str[6], buf[500];
  
  eid_str(str, zone->eid);
  cat_str_3("zone: %s; path: %i; path pt: %i;\n", str, path_idx, 
          path_pt_idx);
  cat_vec(cam_rot);

  header = (zone_header*)zone->items[0];
  dim = (zone_dimensions*)zone->items[1];

  path = (zone_path*)zone->items[header->paths_idx + path_idx];
  path_pt = &path->points[path_pt_idx];
  
  if (cam_rot.x == 0 && cam_rot.y == 0 && cam_rot.z == 0) {
    cam_trans.x = (dim->x + path_pt->x) << 8;
    cam_trans.y = (dim->y + path_pt->y) << 8;
    cam_trans.z = (dim->z + path_pt->z) << 8;
    cam_rot.x = path_pt->rot_x;
    cam_rot.y = path_pt->rot_y;
    cam_rot.z = path_pt->rot_z;
  }
  else {
    cam_trans.x += dim->x << 8;
    cam_trans.y += dim->y << 8;
    cam_trans.z += dim->z << 8;
  }
  
  mat33_rotation(&m_cam_rot, cam_rot);
    
  // apply additional scaling
  ms_cam_rot[0][0] = m_cam_rot[0][0];
  ms_cam_rot[0][1] = m_cam_rot[0][1];
  ms_cam_rot[0][2] = m_cam_rot[0][2];
  ms_cam_rot[1][0] = -(5*m_cam_rot[1][0])/8;
  ms_cam_rot[1][1] = -(5*m_cam_rot[1][1])/8;
  ms_cam_rot[1][2] = -(5*m_cam_rot[1][2])/8;
  ms_cam_rot[2][0] = -m_cam_rot[2][0];
  ms_cam_rot[2][1] = -m_cam_rot[2][1];
  ms_cam_rot[2][2] = -m_cam_rot[2][2];
  
  cat_mat(ms_cam_rot);
  cat_vec(cam_trans);

  for (i=0;i<header->world_count;i++) {
    world = nsf_entry(nsf, header->worlds[i].wgeo);
    eid_str(str, world->eid);
    cat_str_2("world %s (%i)\n", str, i);
  }
  
  if (poly_ids) {
    world_poly_count = 1;
    for (i=0;i<*poly_count;i++,polys++) {
      poly_id = poly_ids[i];
      world = nsf_entry(nsf, header->worlds[poly_id.world_idx].wgeo);
      wgeo_project_stats(world, cam_trans, ms_cam_rot, screen_offset, 
                   &poly_id, polys, &world_poly_count, stats);
    }
    return;
  }
  
  *poly_count = 0;
  for (i=0;i<header->world_count;i++) {
    world = nsf_entry(nsf, header->worlds[i].wgeo);
    wgeo_project_stats(world, cam_trans, ms_cam_rot, screen_offset, 
                 0, polys, &world_poly_count, stats);
    polys += world_poly_count;
    *poly_count += world_poly_count;
  }
}

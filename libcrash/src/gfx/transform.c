/**
 * software-based implementation of geometry transformation routines 
 * used in the crash games
 */ 
#include "gfx.h"
#include "entry/wgeo.h"
#include "entry/zdat.h"

#include "gte.h"
extern psxGTERegisters psxRegs;

#undef DEBUG_GFX

#include <stdio.h>

/**
 * matrix transforms a 3-dimensional point
 * 
 * expects the coordinates of matrix and point to be fixed point values
 * with a 12 bit fractional part. returns the result point also in 12 bit
 * fractional part fixed point format (hence the right shift)
 * 
 * [multiplying 2 respective 12 bit fractional part fixed point 
 * values of a matrix entry and vector component produces a 24 bit 
 * fractional part fixed point result so it is necessary to shift right
 * to restore the correct precision]
 */
// inline static pnt32 mat33_transform(int16_t mat[3][3], pnt32 pnt) {
pnt32 mat33_transform(int16_t mat[3][3], pnt32 pnt) {
  pnt32 t_pnt;
  
  t_pnt.x = ((mat[0][0]*pnt.x)+(mat[0][1]*pnt.y)+(mat[0][2]*pnt.z))>>12;
  t_pnt.y = ((mat[1][0]*pnt.x)+(mat[1][1]*pnt.y)+(mat[1][2]*pnt.z))>>12;
  t_pnt.z = ((mat[2][0]*pnt.x)+(mat[2][1]*pnt.y)+(mat[2][2]*pnt.z))>>12;

  return t_pnt;
}

/** 
 * calculates the rotation matrix for a ZXY Tait-Bryan angle 
 *
 * the components of the angle [vector] are values such that the range
 * from 0 to 2pi has been scaled to 0 to 4096 (?)
 *
 * values of the returned matrix are in 12 bit fractional part fixed 
 * point format
 */  
// inline static void mat33_rotation(int16_t (*mat)[3][3], ang32 rot) {
void mat33_rotation(int16_t (*mat)[3][3], ang32 rot) {
  int16_t s1,s2,s3,c1,c2,c3;
  int16_t c1c3,s1s2,c2s1,c1s3,c3s1,c1s2,c1c2,s1s3,c2s3,c2c3;
  int16_t s1s2s3,c3s1s2,c1s2s3,c1c3s2;
  
  s1 = ang16_sin(-rot.z);
  s2 = ang16_sin(-rot.x);
  s3 = ang16_sin(-rot.y);
  c1 = ang16_cos(-rot.z);
  c2 = ang16_cos(-rot.x);
  c3 = ang16_cos(-rot.y);
  
  c1c3 = (c1 * c3) >> 12;
  s1s2 = (s1 * s2) >> 12;
  c2s1 = (c2 * s1) >> 12;
  c1s3 = (c1 * s3) >> 12;
  c3s1 = (c3 * s1) >> 12;
  c1s2 = (c1 * s2) >> 12;
  c1c2 = (c1 * c2) >> 12;
  s1s3 = (s1 * s3) >> 12;
  c2s3 = (c2 * s3) >> 12;
  c2c3 = (c2 * c3) >> 12;
  
  s1s2s3 = (s1s2 * s3) >> 12;
  c3s1s2 = (c3s1 * s2) >> 12;
  c1s2s3 = (c1s2 * s3) >> 12;
  c1c3s2 = (c1c3 * s2) >> 12;
  
  (*mat)[0][0] = c1c3 - s1s2s3;
  (*mat)[0][1] = -c2s1;
  (*mat)[0][2] = c1s3 + c3s1s2;
  (*mat)[1][0] = c3s1 + c1s2s3;
  (*mat)[1][1] = c1c2;
  (*mat)[1][2] = s1s3 - c1c3s2;
  (*mat)[2][0] = -c2s3;
  (*mat)[2][1] = s2;
  (*mat)[2][2] = c2c3;
}

/**
 * projects a world model to screen coordinates 
 * 
 * world         - world model entry
 * cam_trans     - camera trans vector
 * ms_cam_rot    - camera [scaled] rotation matrix
 * screen_offset - vector. x and y coords are final 2d offset to add to
 *                 pixel coords and z coord is the z coord scale factor
 *                 to use when computing w coords (varies per nsd/lid)
 * poly_ids      - ids of polygons to project or zero if projecting all
 *                 polygons 
 * polys         - pre-allocated buffer for storing the result polygons
 * poly_count    - (in/out) number of result polygons
 */
void wgeo_project(entry *world, 
                  vec32 cam_trans, int16_t ms_cam_rot[3][3], 
                  vec32 screen_offset,
                  int normalize, int pcsx,
                  poly_id *poly_ids, fpoly *polys, int *poly_count) {
  int i, ii, p;
  wgeo_header *header;
  wgeo_polygon *poly, *wpolys;
  wgeo_vertex *vert, *verts;
  pnt32 u_viewmodel, r_viewmodel, r_vert, u_vert, u_vert32, v_vert32;
  pnt16 v_vert;
  fpnt s_vert, t_vert;
  int32_t z13;
  int vert_idx[3];
  int x10,x20,y10,y20,z10,z20;
#ifdef DEBUG_GFX
  FILE *out;
#endif
  
  header = (wgeo_header*)world->items[0];
  //if (getWord(worldheader, 0x1C, true) == 1) { continue; }
  
  u_viewmodel.x = header->trans_x - (cam_trans.x >> 8);
  u_viewmodel.y = header->trans_y - (cam_trans.y >> 8);
  u_viewmodel.z = header->trans_z - (cam_trans.z >> 8);
  
  // use camera rot matrix to transform ((model relative) unrotated 
  // view coords to (rotated model relative) view coords) 
  // (game code uses the exact logic for mat33_transform  to do the rot)
  r_viewmodel = mat33_transform(ms_cam_rot, u_viewmodel);

#ifdef DEBUG_GFX
  out = fopen("temp_gfx.txt", "a+");
  fprintf(out, "%i, %i, %i\n", u_viewmodel.x, u_viewmodel.y, u_viewmodel.z);
  fprintf(out, "%i, %i, %i\n", r_viewmodel.x, r_viewmodel.y, r_viewmodel.z);
#endif
  
  wpolys = (wgeo_polygon*)world->items[1];
  verts = (wgeo_vertex*)world->items[2];
  
  if (!poly_ids) { *poly_count = header->poly_count; }
  if (pcsx) {
    psxRegs.CP2C.n.ofx = 0;
    psxRegs.CP2C.n.ofy = 0;
    psxRegs.CP2C.n.h = screen_offset.z;
    psxRegs.CP2C.n.trX = r_viewmodel.x;
    psxRegs.CP2C.n.trY = r_viewmodel.y;
    psxRegs.CP2C.n.trZ = r_viewmodel.z;
    
    psxRegs.CP2C.n.rMatrix.m11 = ms_cam_rot[0][0];
    psxRegs.CP2C.n.rMatrix.m12 = ms_cam_rot[0][1];
    psxRegs.CP2C.n.rMatrix.m13 = ms_cam_rot[0][2];
    psxRegs.CP2C.n.rMatrix.m21 = ms_cam_rot[1][0];
    psxRegs.CP2C.n.rMatrix.m22 = ms_cam_rot[1][1];
    psxRegs.CP2C.n.rMatrix.m23 = ms_cam_rot[1][2];
    psxRegs.CP2C.n.rMatrix.m31 = ms_cam_rot[2][0];
    psxRegs.CP2C.n.rMatrix.m32 = ms_cam_rot[2][1];
    psxRegs.CP2C.n.rMatrix.m33 = ms_cam_rot[2][2];
    for (i=0;i<*poly_count;i++) {
      poly = poly_ids ? &wpolys[poly_ids[i].poly_idx] 
                      : &wpolys[i];
      vert_idx[0] = poly->a_idx;
      vert_idx[1] = poly->b_idx;
      vert_idx[2] = poly->c_idx;

      for (ii=0;ii<3;ii++) {
        vert = &verts[vert_idx[ii]];
        z13 = vert->z8+(vert->z2<<8)+(vert->z3<<10);
      
        psxRegs.CP2D.p[ ii << 1 ].sw.l = (int16_t)(vert->x << 3);
        psxRegs.CP2D.p[ ii << 1 ].sw.h = (int16_t)(vert->y << 3);
        psxRegs.CP2D.p[ (ii << 1) + 1 ].sw.l = (int16_t)(z13 << 3);
      }
      
      psxRegs.code = 0x280030;
      gteRTPT();
   
      for (ii=0;ii<3;ii++) {
        s_vert.xi = psxRegs.CP2D.p[ 12+ii ].sw.l;
        s_vert.yi = psxRegs.CP2D.p[ 12+ii ].sw.h;
        s_vert.zi = psxRegs.CP2D.p[ 17+ii ].w.l;
        t_vert.zi = h_over_z(ii);
      
        if (normalize) {
          s_vert.x = (float)s_vert.xi / screen_offset.x;
          s_vert.y = (float)s_vert.yi / screen_offset.y;
          s_vert.z = (float)s_vert.zi;  // just to ensure they are all floats
        }
        else {
          s_vert.xi += screen_offset.x;
          s_vert.yi += screen_offset.y;
        }
        
#ifdef DEBUG_GFX
        vert = &verts[vert_idx[ii]];
        z13 = vert->z8+(vert->z2<<8)+(vert->z3<<10);
        
        u_vert.x=(int16_t)(vert->x << 3);
        u_vert.y=(int16_t)(vert->y << 3); 
        u_vert.z=(int16_t)(z13 << 3);
         
        // TODO: r_vert, v_vert
        fprintf(out, "%i, %i, %i, %i, %i, ",
          poly_id_val(poly_ids[i]), ii, verts->x, vert->y, z13);
        fprintf(out, "%i, %i, %i, %i, %i, %i, ", 
          u_vert.x, u_vert.y, u_vert.z, r_vert.x, r_vert.y, r_vert.z);
        fprintf(out, "%i, %i, %i, %f, %f, %f\n", 
          v_vert.x, v_vert.y, v_vert.z, s_vert.x, s_vert.y, s_vert.z); 
#endif
        polys[i].verts[ii] = s_vert;
        polys[i].vertuvws[ii] = t_vert;
      }
    }
    return;
  }
      
  for (i=0;i<*poly_count;i++) {
    poly = poly_ids ? &wpolys[poly_ids[i].poly_idx] 
                    : &wpolys[i];
    vert_idx[0] = poly->a_idx;
    vert_idx[1] = poly->b_idx;
    vert_idx[2] = poly->c_idx;
 
    polys[i].pad2 = 0;
    for (ii=0;ii<3;ii++) {
      vert = &verts[vert_idx[ii]];
      z13 = vert->z8+(vert->z2<<8)+(vert->z3<<10);
      
      u_vert.x = (int16_t)(vert->x << 3); // convert to 16 bit signed
      u_vert.y = (int16_t)(vert->y << 3); // before storing as 32 bit
      u_vert.z = (int16_t)(z13 << 3);     // signed
      
      // use cam rot mat to transform (model to rotated model coords)
      r_vert = mat33_transform(ms_cam_rot, u_vert);
      
      v_vert32.x = r_viewmodel.x + r_vert.x;
      v_vert32.y = r_viewmodel.y + r_vert.y;
      v_vert32.z = r_viewmodel.z + r_vert.z;
              
      // offset rotated model relative view coords to yield view 
      // coords; [rot vert coords = rot model coords]
      v_vert.x = r_viewmodel.x + r_vert.x; // note the limiting to 16 bits, per the gte calculations
      v_vert.y = r_viewmodel.y + r_vert.y;
      v_vert.z = r_viewmodel.z + r_vert.z;
   
         
      // project view to screen coords
      t_vert.z = (double)(screen_offset.z << 16) / 
                 (double)(v_vert.z ? v_vert.z : 0.0000001f);
      s_vert.x = ((screen_offset.x << 16) +
                  (signed long long)(v_vert.x * t_vert.z)) >> 16;
      s_vert.y = ((screen_offset.y << 16) + 
                  (signed long long)(v_vert.y * t_vert.z)) >> 16;
      s_vert.z = v_vert.z; // no proj for z
      
      // t_vert.z = integer
      // s_vert.x = integer in range 0 to screen_offset.x*2
      // s_vert.y = integer in range 0 to screen_offset.y*2
      // v_vert.x = fixed point (16,16)
      // v_vert.y = fixed point (16,16)
      // 
      // 
      
      // s_x = ofx + (v_x * (ofz / v_z))
      // s_y = ofy + (v_y * (ofz / v_z))
      // s_z = v_z
      
      // in clipping stage
      // s_x = (v_x * (ofz / v_z))
      // s_y = (v_y * (ofz / v_z))
      // s_z = v_z
      
      // clip does the following for any vert with sa_z < 0
      
      // t = -sa_z/sb_z-sa_z
      // s_x = sa_x + (-sa_z/(sb_z-sa_z))*(sb_x - sa_x)
      // s_y = sa_y + (-sa_z/(sb_z-sa_z))*(sb_y - sa_y)
      // s_z = 0
      //
      // which is really
      // s_x = (va_x * (ofz/va_z)) + (-va_z/(vb_z-va_z))*((vb_x * (ofz/vb_z)) - (va_x * (ofz/va_z)))
      
      // s_x = 
      
      // update: unnormalized screen coords off by (512, 384)? should be
      // subtracted?
      
      // edit: difference is game does not use screen_offset? or 
      // screen_offset = (0,0). coords intepreted by the gpu are partially
      // normalized? in the range (-256,-128) to (256,128) are onscreen,
      // with (0,0) at the center.
      // for here however screen coords are in the range (0,0) to (w,h),
      // so screen_offset = (w/2,h/2) and the range (-w/2,-h/2) to (w/2,h/2)
      // is shifted to the range (0,0) to (w,h) temporarily as unnormalized
      // coordinates, and then back to (-1.0,-1.0) to (1.0,1.0) after
      // normalization
      // so in comparing we should consider that the unnormalized game
      // coords do not have the shift like the code here
#ifdef DEBUG_GFX
      fprintf(out, "%i, %i, %i, %i, %i, ",
        poly_id_val(poly_ids[i]), ii, vert->x, vert->y, z13);
      fprintf(out, "%i, %i, %i, %i, %i, %i, ", 
        u_vert.x, u_vert.y, u_vert.z, r_vert.x, r_vert.y, r_vert.z);
      fprintf(out, "%i, %i, %i, %f, %f, %f\n", 
        v_vert.x, v_vert.y, v_vert.z, s_vert.x, s_vert.y, s_vert.z);
#endif

      if (normalize) {
        s_vert.x = (s_vert.x/screen_offset.x) - 1.0;
        s_vert.y = 1.0 - (s_vert.y/screen_offset.y);
      }
       
      polys[i].verts[ii] = s_vert;
      polys[i].vertuvws[ii] = t_vert;
    }
    
    x10 = polys[i].verts[1].x - polys[i].verts[0].x;
    y10 = polys[i].verts[1].y - polys[i].verts[0].y;
    z10 = polys[i].verts[1].z - polys[i].verts[0].z;
    x20 = polys[i].verts[2].x - polys[i].verts[0].x;
    y20 = polys[i].verts[2].y - polys[i].verts[0].y;
    z20 = polys[i].verts[2].z - polys[i].verts[0].z;
    if (-polys[i].verts[0].x * (y10*z20 - z10*y20)
        - polys[i].verts[0].y * (z10*x20 - x10*z20)
        - polys[i].verts[0].z * (x10*y20 - y10*x20) >= 0)
      polys[i].pad1 = 1;
    else
      polys[i].pad1 = 0;

    // // stuff below to enable in case we want clipping at this stage
    // poly_indices[i] = i;
    
    /*
    distz = (0x800 - (screenoffset.z/2)) - 
               ((polys[*(poly_count)].verts[0].z + 
                 polys[*(poly_count)].verts[1].z + 
                 polys[*(poly_count)].verts[2].z) / 32);
    miny = min_3(polys[*(poly_count)].verts[0].y, 
                 polys[*(poly_count)].verts[1].y,
                 polys[*(poly_count)].verts[2].y);
  
    for (uint32_t iii=0; iii<3; iii++)
    {
      // add the poly to the list if any of its verts lie onscreen 
      if (test_bounds2(polys[*poly_count].verts[ii].x, 
                       polys[*poly_count].verts[ii].y, 
                       -64, -112, 256, 224)) {      
        poly_indices[(*poly_count)++] = polyid;
        break;
      }
    }
    */
  }
#ifdef DEBUG_GFX
  fclose(out);
#endif
}

/**
 * projects the world models in a zone to screen coordinates
 * 
 * the camera trans vector and rot matrix used for the projection are 
 * calculated from the relative location and orientation for the 
 * specified camera path point, relative to the zone location
 * 
 * nsf           - nsf structure
 * zone          - zone entry
 * path_idx      - index of path in zone
 * path_pt_idx   - index of point in path with the relative camera
 *                 location (trans) and orientation (rot)
 * screen_offset - screen offset vector (see wgeo_project)
 * cam_trans     - overrides the relative location from the path point 
 *                 if cam_rot is nonzero
 * cam_rot       - overrides the orientation from the path point if 
 *                 nonzero
 * poly_ids      - ids of polygons to project or zero if projecting all 
 *                 polygons
 * polys         - pre-allocated buffer for storing the result polygons
 * poly_count    - (in/out) number of result polygons
 */ 
void zdat_project(nsf *nsf, entry *zone, int path_idx, int path_pt_idx, 
                  vec32 screen_offset, vec32 cam_trans, ang32 cam_rot,
                  int normalize, int pcsx,
                  poly_id *poly_ids, fpoly *polys, int *poly_count) {
                    
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
#ifdef DEBUG_GFX
  FILE *out;
#endif

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

#ifdef DEBUG_GFX
  out = fopen("temp_gfx.txt", "w");
  fprintf(out, "%i, %i, %i\n", cam_trans.x, cam_trans.y, cam_trans.z);
  fprintf(out, "%i, %i, %i\n", cam_rot.x, cam_rot.y, cam_rot.z);
  fprintf(out, "%i, %i, %i\n", m_cam_rot[0][0], m_cam_rot[0][1], m_cam_rot[0][2]);
  fprintf(out, "%i, %i, %i\n", m_cam_rot[1][0], m_cam_rot[1][1], m_cam_rot[1][2]);
  fprintf(out, "%i, %i, %i\n", m_cam_rot[2][0], m_cam_rot[2][1], m_cam_rot[2][2]);
  fprintf(out, "%i, %i, %i\n", ms_cam_rot[0][0], ms_cam_rot[0][1], ms_cam_rot[0][2]);
  fprintf(out, "%i, %i, %i\n", ms_cam_rot[1][0], ms_cam_rot[1][1], ms_cam_rot[1][2]);
  fprintf(out, "%i, %i, %i\n", ms_cam_rot[2][0], ms_cam_rot[2][1], ms_cam_rot[2][2]);
  fclose(out);
#endif
  
  if (poly_ids) {
    world_poly_count = 1;
    for (i=0;i<*poly_count;i++,polys++) {
      poly_id = poly_ids[i];
      if (header->worlds[poly_id.world_idx].key & 1)
        world = nsf_entry(nsf, header->worlds[poly_id.world_idx].eid);
      else
        world = header->worlds[poly_id.world_idx].entry;
      wgeo_project(world, cam_trans, ms_cam_rot, screen_offset, 
                   normalize, pcsx,
                   &poly_id, polys, &world_poly_count);
    }
    return;
  }
  
  *poly_count = 0;
  for (i=0;i<header->world_count;i++) {
    if (header->worlds[i].key & 1)
      world = nsf_entry(nsf, header->worlds[i].eid);
    else
      world = header->worlds[i].entry;
    wgeo_project(world, cam_trans, ms_cam_rot, screen_offset, 
                 normalize, pcsx,
                 0, polys, &world_poly_count);
    polys += world_poly_count;
    *poly_count += world_poly_count;
  }
}

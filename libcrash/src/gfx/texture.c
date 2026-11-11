uint32_t pixel_5551_8888(uint16_t p, int mode) {
  int r,g,b,a;
  
  r = (p >> 0) & 0x1F;
  g = (p >> 5) & 0x1F;
  b = (p >> 10) & 0x1F;
  a = (p >> 15) & 1;
  
  r = (r << 4) + r;
  g = (g << 4) + g;
  b = (b << 4) + b;
  
  switch (mode) {
  case 0: a = a == 1 ? 0x7F : r+g+b == 0 ? 0 : 0xFF; break;
  case 1: a = a == 1 ? 0xFF : r+g+b == 0 ? 0 : 0xFF; break;
  case 2: a = a == 1 ? 0xFF : r+g+b == 0 ? 0 : 0xFF; break;
  case 3: a = a == 1 ? 0xFF : r+g+b == 0 ? 0 : 0xFF; break;
  }
  return (a << 24) | (r << 16) | (g << 8) | b;
}

const uint32_t pos_masks[6] = { 0x30FF0C, 0xF3CC30, 0x8799E1, 
                                0x9E7186, 0x4B66D2, 0x6DB249 };
	                               
typedef struct {
  texinfo texinfo;
  int texid;
  fpnt uvs[3];
  rect2d rect;
} tex_cache_entry;

typedef struct {
  avl_tree tree;
  int entry_count;
  tex_cache_entry[...] entries;
  int tpage_count;
  eid_t tpages[8];
  uint32_t *data[48];
  uint8_t _data[8*3584*512];
} tex_cache;

tex_cache tex_cache;

static void texture_cache_init() {
  int i, j;
  uint8_t *data;
  
  avl_tree_init(&tex_cache.tree);
  tex_cache.entry_count = 0;
  tex_cache.tpage_count = 0;
  data = tex_cache._data;
  for (i=0;i<8;i++) {
    for (j=0;j<6;j++) {
      tex_cache.data[(i*6)+j] = (uint32_t*)data;
      data += 1 << (19 - (j%3));
    }
  }
}    

int texture_new(texinfo *texinfo, fpnt (*uvs)[3]) {
  int i, ppi, fw;
  float page_width;
  rect2d rect;
  pnt32 clut;
  int pgidx;
  tpage *tpage;
  tex_cache_entry *entry;
  
  ppi = (2 << (2 - texinfo->color_mode));
  fw = texinfo->uv_idx / 25;
  page_width = (float)(ppi << 7);
  
  rect.x = ((texinfo->segment * 32) + texinfo->xoffs) * ppi;
  rect.y = texinfo->yoffs * 4;
  rect.w = 4 << (texinfo->uv_idx % 5);
  rect.h = 4 << ((texinfo->uv_idx / 5) % 5);
 
  for (i=0;i<3;i++) {
    uvs[i].x = (rect.x+(rect.w*((pos_masks[(i<<1)+0]>>fw)&1))) / page_width;
    uvs[i].y = (rect.y+(rect.h*((pos_masks[(i<<1)+1]>>fw)&1))) / 128.0;
  }
  
  clut.x = texinfo->clut_x;
  clut.y = texinfo->clut_y;
  
  tpage = nsf->entry(texinfo->tpage);
  pgidx = texture_data(tpage, rect, clut, 
                       texinfo->color_mode, texinfo->blend_mode);   

  entry = &tex_cache.entries[tex_cache.entry_count++];
  entry->texinfo = *texinfo;
  entry->pgidx = pgidx;
  entry->uvs = *uvs;
  entry->rect = rect;
  
  // TODO: compute hash here
  
  avl_tree_insert(&tex_cache.tree, hash, entry);
}

int texture_lookup(texinfo *texinfo, fpnt (*uvs)[3]) {
  tex_cache_entry *entry;
  
  // TODO: compute hash here
  entry = avl_tree_search(&tex_cache.tree, hash);
  if (!entry) {
    return -1;
  }
  
  *uvs = entry->uvs;
  return entry->pgidx;
  
int texture_load(texinfo *texinfo, fpnt (*uvs)[3]) {
  int id;
  
  id = texture_lookup(texinfo, uvs);
  if (id != -1) return id;
  
  id = texture_new(texinfo, uvs);
  return id;
}

/**
 * copies a rect of pixels inside tpage into the texture cache
 * 
 * returns index of the cache texture page to which the data is copied
 */
int texture_data(tpage *tpage, rect2d rect, pnt32 clut, 
                 int color_mode, int blend_mode) {
  int i, idx, texid;
  uint32_t *data, palette[256];
  uint8_t *tpage_data;
  uint16_t *tpage_data_16;
  uint16_t *clut_data;
  
  for (i=0;i<tex_cache.tpage_count;i++)
    if (tex_cache.tpages[i] == tpage) break;
  if (i == tex_cache.tpage_count && i < 7)
    tex_cache.tpages[i] = tpage;
  
  texid = i*6 + (color_mode + blend_mode == 0 ? 3 : 0);
  data = (uint32_t*)&tex_cache.data[texid];
  tpage_data = (uint8_t*)tpage;
  tpage_data_16 = (uint16_t*)tpage_data;
  clut_data = (uint16_t*)&tpage_data[clut.x*32+clut.y*512];
  
  switch (color_mode) {
  case 0:
    for (i=0;i<16;i++)
      palette[i] = pixel_5551_8888(&clut_data[i], blend_mode);
    for (y=0;y<rect.h;y++) {
      for (x=0;x<rect.w;x++) {
        idx = (rect.x/2)+x+(rect.y+y)*512;
        data[(idx*2)+0] = palette[(tpage_data[idx] >> 0) & 0xF];
        data[(idx*2)+1] = palette[(tpage_data[idx] >> 4) & 0xF];
      }
    }
    break;
  case 1:
    for (i=0;i<256;i++)
      palette[i] = pixel_5551_8888(&clut_data[i], blend_mode);
    for (y=0;y<rect.h;y++) {
      for (x=0;x<rect.w;x++) {
        idx = rect.x+x+(rect.y+y)*512;
        data[idx] = pixel_5551_8888(palette[tpage_data[idx]], blend_mode);
      }
    }
    break;
  case 2:
    for (y=0;y<rect.h;y++) {
      for (x=0;x<rect.w;x++) {
        idx = rect.x+x+(rect.y+y)*256;
        data[idx] = pixel_5551_8888(tpage_data_16[idx], blend_mode); 
      }
    }
    break;
  }
  return idx;
}

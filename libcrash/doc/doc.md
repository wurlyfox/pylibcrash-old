#libcrash
##directory structure

- /libcrash/include/*.h - headers for ns hierarchy structures. also gfx
  - nsf.h
  - nsd.h
  - page.h
  - entry.h
  - gfx.h

- /libcrash/include/entry/*.h - headers for entry structures
  - svtx.h
  - tgeo.h
  - wgeo.h
  - slst.h
  - zdat.h
  - gool.h

- /libcrash/src/*.c - sources for nsd hierarchy structure functions
  - nsf.c
  - nsd.c
  - page.c
  - entry.c 
   
- /libcrash/src/entry/*.c - sources for entry structure functions
  - slst.c
  
- /libcrash/src/gfx/*.c - sources for gfx functions
  - transform.c
  - rasterize.c
  - sin.c
  
- /libcrash/test - unit tests
  
##API

###read
converts raw data to structure 

```extern nsf *nsf_read(uint8_t *data, nsd *nsd);```<br>
```extern nsd *nsd_read(uint8_t *data);```<br>
```extern page *page_read(uint8_t *data);```<br>
```extern entry *entry_read(uint8_t *data);```<br>

###write 
converts structure to raw data

``extern uint8_t *nsf_write(nsf *nsf, nsd *nsd, size_t *size);``<br>
``extern uint8_t *nsd_write(nsd *nsd, size_t *size);``<br>
``extern uint8_t *page_write(page *pg);``<br>
``extern uint8_t *entry_write(entry *en);``<br>

###unpack 
moves referenced objects out to separately allocated blocks

``extern nsd *nsd_unpack(nsd *nsd, int page_table_len, nsd_ldat *ldat);``<br>
``extern page *page_unpack(page *pg, int flags);``<br>
``extern entry *entry_unpack(entry *en, int flags);``<br>

###pack 
packs an object and all objects which it references into a contiguous block
       
``extern nsd *nsd_pack(nsd *nsd, nsd_ldat *ldat);``<br>
``extern page *page_pack(page *pg, int flags);``<br>
``extern entry *entry_pack(entry *en, int flags);``<br>

###constructors/allocators/initializers

``extern nsd *nsd_new(int page_table_len);``<br>

``extern page *page_init(page *pg, int idx);``<br>

``extern entry *entry_alloc(int item_count);``<br>
``extern entry *entry_init(entry *en, eid_t eid, int type);``<br>

###lookup

``extern page *nsf_page(nsf *nsf, pgid_t pgid); // get page by id``<br>
``extern page *nsf_texture_page(nsf *nsf, eid_t eid);``<br>
``extern entry *nsf_entry(nsf *nsf, eid_t eid);``<br>
``extern int nsf_entry_idx(nsf *nsf, eid_t eid, pgid_t pgid);``<br>

``extern nsd_pte *nsd_lookup(nsd *nsd, eid_t eid);``<br>
``extern pgid_t nsd_lookup_pgid(nsd *nsd, eid_t eid);``<br>
``extern eid_t nsd_global_eid(nsd *nsd, int idx);``<br>
``extern int nsd_global_eid_idx(nsd *nsd, eid_t eid);``<br>

###build nsd and nsf

``extern nsd_pte *nsd_pte_new(nsd *nsd, entry *en, pgid_t pgid);``<br>
``extern entry *nsd_entry_new(nsd *nsd, eid_t eid, int type, int);``<br>

``extern nsf *nsf_new(nsd *nsd);``<br>
``extern page *nsf_page_new(nsf *nsf, int flags);``<br>

###misc

``extern size_t page_compressed_size(page_compressed *page_src);``<br>
``extern void page_decompress(page *page_dst, page_compressed *page_src);``<br>
``extern void page_compress(page *page_src, page_compressed *page_dst);``<br>

``extern size_t entry_size(entry *en);``<br>
``extern size_t entry_item_size(entry *en, int idx);``<br>

``extern void eid_str(char *str, eid_t eid);``<br>
``extern void str_eid(char *str, eid_t *eid);``<br>

###entry functions

``extern void slst_decode_forward(entry *slst, int idx, 
                                poly_id *src, poly_id *dst, 
                                int src_len, int *dst_len,
                                slst_callbacks *callbacks);``<br><br>
``extern void slst_decode_backward(entry *slst, int idx, 
                                 poly_id *src, poly_id *dst, 
                                 int src_len, int *dst_len,
                                 slst_callbacks *callbacks);``<br><br>
``extern slst *slst_encode(poly_id *src, poly_id *dst, 
                         int src_len, int dst_len,
                         size_t *slst_size);``<br>

``extern void wgeo_project(entry *world, 
                  vec32 cam_trans, int16_t ms_cam_rot[3][3], 
                  vec32 screen_offset,
                  int normalize,
                  poly_id *poly_ids, fpoly *polys, int *poly_count);``<br><br>
``extern void zdat_project(nsf *nsf, entry *zone, int path_idx, int path_pt_idx, 
                  vec32 screen_offset, vec32 cam_trans, ang32 cam_rot,
                  int normalize,
                  poly_id *poly_ids, fpoly *polys, int *poly_count);``<br><br>

##Notes

When creating a new unpacked object, for each variable length array, 
space must be allocated for the maximum number of items. The unused 
space will be truncated when the object is packed. The maximum number
of items is to be passed as an argument to the object constructor.

If we wish to insert to/remove from a variable length array in an object 
that is already packed, then the object must first be unpacked and then
reallocated to fit the new/truncate the old items. (assuming the vla is 
a flexible array at the end of the structure)

#ifndef NSF_H
#define NSF_H

#include "types.h"
#include "nsd.h"

typedef struct {
  union {
    nsd *dir;
    uint8_t data[0];
  };
} nsf;

extern nsf *nsf_read(uint8_t *data, nsd *nsd);
extern uint8_t *nsf_write(nsf *nsf, nsd *nsd, size_t *size);

extern page *nsf_page(nsf *nsf, pgid_t pgid);
extern page *nsf_texture_page(nsf *nsf, eid_t eid);

extern entry *nsf_entry(nsf *nsf, eid_t eid);
extern entry *_nsf_entry(nsf *nsf, eid_t eid, pgid_t pgid);
extern int nsf_entry_idx(nsf *nsf, eid_t eid, pgid_t pgid);

extern page *nsf_page_new(nsf *nsf, int flags);
extern nsf *nsf_new(nsd *nsd);

#endif

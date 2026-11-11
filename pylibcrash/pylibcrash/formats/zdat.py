import sys
sys.path.append('/home/user/src/ctypemap')
from ctypemap.base import Packable

from libcrash import ffi
from pylibcrash.entry import Entry

import numpy as np

class ZoneHeader(Packable):
    field_map = {
        'worlds': {
            'count': 'world_count'
        },
        'neighbor': {
            'count': 'neighbor_count'
        },
        'tpage': {
            'count': 'tpage_count'
        },
        'tchunk': {
            'count': 'tchunk_count'
        }
    }
        
class ZoneDimensions(Packable):
    field_map = {
        'collisions': {
            'pack': ('internal', 0)
        }
    }
                
class ZoneCollisions(Packable):
    field_map = {
        'nodes': {
            'count': '$remainder',
            'pack': ('internal', 0)
        }
    }
        
class ZonePathPoint(Packable):
    pass
        
class ZonePath(Packable):
    field_map = {
        '$fixed_size': 50, # workaround
        'neighbor_paths': {
            'count': 'neighbor_path_count'
        },
        'points': {
            'count': 'length',
            'pack': ('internal', 0)
        }
    }
                                 
class ZoneEntityPathPoint(Packable):
    pass

class ZoneEntityNull(Packable):
	pass
	 
class ZoneEntity(Packable):
    field_map = {
        'path_points': {
            'count': 'path_point_count',
            'pack': ('internal', 0)
        },
        'null': {
            'type': 'zone_entity_null',
            'pack': ('internal', 1)
        }
    }

class ZoneWorld(Packable):
    pass
        
class ZoneBounds(Packable):
    pass
        
class ZoneNeighborPath(Packable):
    pass
        
def zone_header_item(cobj):
    obj_ptr = ffi.cast("uint8_t*", ffi.addressof(cobj)) 
    offset = cobj.item_offsets[0]
    if offset < 0x10000:
        item_ptr = obj_ptr + offset
    else:
        item_ptr = offset
    item = ffi.cast("zone_header *", item_ptr)
    return item

class Zone(Entry):
    subclass_id = 7
    field_map = Entry.extend_field_map()
    field_map['item_data']['partitions'] = {
        'header': {
            'type': 'zone_header',
            'pack': ('internal', 0)
        },
        'dimensions': {
            'type': 'zone_dimensions',
            'pack': ('internal', 1),
        },
        'paths': {
            'count': (lambda c: zone_header_item(c).path_count,
                      lambda p,v: setattr(p.header, 'path_count', v)),
            'type': 'zone_path',
            'pack': ('internal', 2)
        },
        'entities': {
            'count': (lambda c: zone_header_item(c).entity_count,
                      lambda p,v: setattr(p.header, 'entity_count', v)),
            'type': 'zone_entity',
            'pack': ('internal', 3)
        }
    }
    @property
    def worlds(self):
        worlds = self.header.worlds
        worlds = [world.eid for world in worlds]
        return worlds

    def get_dependencies(self, nsf):
        exec_map = nsf.dir.ldat.exec_map
        eids = self.worlds + \
               [path.slst for path in self.paths] + \
               [exec_map[entity.type] for entity in self.entities]
        entries = [entry for entry in [nsf.entry(eid, False) 
                    for eid in eids] if entry is not None]
        for idx in range(len(entries)):
            entry = entries[idx]
            dependencies = entry.get_dependencies(nsf)
            entries.extend(dependencies)
        entries = list(set(entries))
        return entries

import sys
sys.path.append('/home/user/src/ctypemap')
from ctypemap.base import Packable

from libcrash import lib, ffi
from pylibcrash.entry import Entry

class WgeoHeader(Packable):
	field_map = {
		'tpags': {
			'count': 'tpag_count'
		}, 
		'texinfos': {
			# note the use of size instead of count, since the array 
			# elements are polymorphic and thus vary in size
			'size': (lambda c: ((c.texinfo_count)*4) + ffi.sizeof(c),
			         lambda p,v: setattr(p, 'texinfo_count', \
						(v - ffi.sizeof(p.cdata)) // 4)),
			'pack': ('internal', 0)
		}
	}

class WgeoPolygon(Packable):
	pass

class WgeoVertex(Packable):
	pass

class WgeoTexinfo(Packable):
	field_map = {
		'$subclass': lambda c: WgeoPalinfo if c.type==0 else None
	}
	
class WgeoPalinfo(Packable):
	pass

def wgeo_header_item(cobj):
    obj_ptr = ffi.cast("uint8_t*", ffi.addressof(cobj)) 
    item_ptr = obj_ptr + cobj.item_offsets[0]
    item = ffi.cast("wgeo_header *", item_ptr)
    return item
    
class Wgeo(Entry):
	subclass_id = 3
	field_map = Entry.extend_field_map()
	field_map['item_data']['partitions'] = {
		'header': {
			'type': 'wgeo_header',
			'pack': ('internal', 0)
		},
		'polygons': {
			'type': {
			    'type': 'wgeo_polygon',
				'count': (lambda c: wgeo_header_item(c).poly_count,
				          lambda p,v: setattr(p.header, 'poly_count', v))
			},
			'pack': ('internal', 1)
		},
		'vertices': {
			'type': {
				'type': 'wgeo_vertex',
				'count': (lambda c: wgeo_header_item(c).vert_count,
				          lambda p,v: setattr(p.header, 'vert_count', v))
			},
			'pack': ('internal', 2)
		}
	}
	
	def get_dependencies(self, nsf):
		entries = [entry for entry in [nsf.entry(tpag, False) 
                   for tpag in self.header.tpags] if entry is not None]
		return entries

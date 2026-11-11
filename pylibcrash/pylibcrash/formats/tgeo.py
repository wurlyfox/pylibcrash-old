import sys
sys.path.append('/home/user/src/ctypemap')
from ctypemap.base import Packable

from libcrash import lib, ffi
from pylibcrash.entry import Entry

class TgeoHeader(Packable):
	field_map = {
		'texinfos': {
			'size': lambda c: ((c.texinfo_count)*4) + ffi.sizeof(c),
			'pack': ('internal', 0)
		}
	}
	
class TgeoPolyon(Packable):
	pass
	
class TgeoTexinfo(Packable):
	field_map = {
		'$subclass': lambda c: TgeoPalinfo if c.type==0 else None
	}
	
class TgeoPalinfo(Packable):
	pass

def tgeo_header_item(cobj):
    obj_ptr = ffi.cast("uint8_t*", ffi.addressof(cobj)) 
    item_ptr = obj_ptr + cobj.item_offsets[0]
    item = ffi.cast("tgeo_header *", item_ptr)
    return item

class Tgeo(Entry):
	subclass_id = 2
	field_map = Entry.extend_field_map()
	field_map['item_data']['partitions'] = {
		'header': {
			'type': 'tgeo_header',
			'pack': ('internal', 0)
		},
		'polygons': {
			'type': {
			    'type': 'tgeo_polygon',
				'count': (lambda c: tgeo_header_item(c).poly_count,
					      lambda p,v: setattr(p.header, 'poly_count', v))
			},
			'pack': ('internal', 1)
		}
	}

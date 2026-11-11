import sys
sys.path.append('/home/user/src/ctypemap')
from ctypemap.base import Packable

from libcrash import lib, ffi
from pylibcrash.entry import Entry

class SvtxFrame(Packable):
	field_map = {
		'vertices': {
			'count': 'length',
			'pack': ('internal', 0)
		}
	}
	
class SvtxVertex(Packable):
	pass

class Svtx(Entry):
	subclass_id = 1
	field_map = Entry.extend_field_map()
	field_map['item_data']['type'] = 'svtx_frame'
	
	def get_dependencies(self, nsf):
		entry = nsf.entry(self.tgeo, False)
		depends = [entry]
		return depends

import sys
sys.path.append('/home/user/src/ctypemap')
from ctypemap.base import Packable

from libcrash import lib, ffi
import numpy as np

class Pgid(Packable):
	def __init__(idx=None):
		if idx is not None: 
			self.value = 1 + (2*idx)
	def __hash__(self):
		return int(self.value)

class Page(Packable):
	# $union: '_entry_data' causes the variable section to begin 
	# at the offset of the _entry_data field (which includes both 
	# offsets and data). 
	# (without this option the structure will be considered fixed format 
	# since _entry_data is at least one subfield of fixed sized within a 
	# union that is the last field of the structure)
	magic = 0x1234
	field_map = {
		'$constants': ['magic'],
		'$subclass': lambda c: TexturePage if c.type==1 else None,
		'$union': '_entry_data',
		'entry_data': {
			'count': 'entry_count',
			'size': '$last_offset',
			'offsets': 'entry_offsets',
			'pointers': 'entries',
			'pack': ('internal', 0)
		}
	}
	
	def __init__(self, idx=0, type=0):
		super().__init__()
		self.type = type
		self.pgid = 1 + (2*idx)
		
	def compress(self):
		if self.packed == False:
			raise Exception("Cannot compress unpacked page.")
		# handle the memory allocation manually for now
		buf = np.zeros(65536, dtype=np.uint8)
		cdata = ffi.cast("page_compressed *", 
			buf.__array_interface__['data'][0])
		lib.page_compress(ffi.addressof(self.cdata), cdata)
		size = lib.page_compressed_size(cdata)
		buf.resize(size, refcheck=False)
		compressed = PageCompressed.from_cbytes(buf)
		# important: associate the buffer with the object; 
		# from_cbytes casts the address of the buffer to a cobj/cdata for
		# processing and therefore reference count is not incremented
		# thus the buffer will be garbage collected unless an explicit 
		# ref to it is held. saving a ref in the object thus ensures
		# that it is destroyed only after the object itself is destroyed
		compressed.__dict__['base'] = buf
		return compressed
		
def page_compressed_varsize(c):
	ptr = ffi.addressof(c)
	size = lib.page_compressed_size(ptr)
	count = size - ffi.sizeof(c)
	return count
	
class PageCompressed(Packable):
	magic = 0x1235
	field_map = {
		'$constants': ['magic'],
		'data': {
			'count': lambda c: page_compressed_varsize(c),
			'pack': ('internal', 0)
		}
	}
	
	def decompress(self):
		if self.packed == False:
			raise Exception("Cannot decompress unpacked compressed page.")
		buf = np.zeros(65536, dtype=np.uint8)
		cdata = ffi.cast("page *", 
			buf.__array_interface__['data'][0])
		lib.page_decompress(ffi.addressof(self.cdata), cdata)
		page = Page.from_cdata(cdata)
		page.__dict__['base'] = buf
		# page = Page()
		# lib.page_decompress(self.cdata, page.cdata)
		# page.reinterpret()
		# return page
	
from pylibcrash.entry import Entry
# this is tricky: a TexturePage is a Page -and- an Entry
# a type 1 page is interpreted as a TexturePage 
# (when calling Page.from_cbytes/data)
# as is a type 5 entry (when calling Entry.from_cbytes/data).
# the underlying tpage structure differs from BOTH page and entry.
# it merges fields of both structures, including the page magic number, 
# page type, eid, entry type, and checksum
class TexturePage(Page, Entry):
	field_map = {}
	subclass_id = 5
	
	def __init__(self, eid):
		super(Page, self).__init__(eid)
		self.type = 1
		self.entry_type = 5
	

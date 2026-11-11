import sys
sys.path.append('/home/user/src/ctypemap')
from ctypemap.base import Packable

from libcrash import ffi
from pylibcrash.nsf import Nsf
from pylibcrash.entry import Entry, Eid

class Lid(Packable):
	pass
	
class NsdLdat(Packable):
	def __init__(self, lid=0):
		self.magic = 1
		self.lid = lid
	
class NsdPte(Packable):
	def __init__(self, entry=None, page=None, pgid=None):
		if entry: self.eid.entry = entry
		if page: self.pgid = page.pgid
		if pgid: self.pgid = pgid
		
class Nsd(Packable):	
	field_map = {
		'page_data': {  # no offsets array implies the structs are fix sized
			'pointer': 'pages',
			'count': 'page_count',
#			'offset': 'pages_offset',
			'varfmt': True,   # forces 
			'pack': ('external', 0, Nsf)  
		},
		'compressed_page_data': {  
			'pointers': 'compressed_pages',
			'count': 'compressed_page_count',
			'offsets': ('compressed_page_offsets', (31,6)),
			'sizes': ('compressed_page_offsets', (5,0)),
			'size': 'pages_offset',
			'unitsize': 2048,
			'pack': ('external', 0, Nsf)
		},
		'page_table': {
			'count': 'page_table_size',
			'pack': ('internal', 0)
		},
		'ldat': {
			'type': 'nsd_ldat',
			'pack': ('internal', 1) 
		}
	}
	
	def lookup_idx(self, eid):
		if eid.value == 0 or eid == Eid.none():
			return None
		idx = eid.bucket_hash
		offset = self.ptb_offsets[idx]
		# hacky thing for now when the offsets are actually pointers
		if self.ptb_offsets[0] > 256:
			offset -= int(ffi.cast("uint32_t", self.cptr))
			offset -= int(ffi.offsetof("nsd", "page_table"))
		for idx in range(offset//8, len(self.page_table)):
			pte = self.page_table[idx]
			if pte.eid.entry is not None and pte.eid.entry.eid == eid:
				return idx
			elif pte.eid == eid:
				return idx
		return None
			
	def lookup(self, eid):
		idx = self.lookup_idx(eid)
		if idx is None:
			return None
		return self.page_table[idx]
	
	def pte_new(self, entry, page=None, pgid=None):
		if self.packed==True:
			raise Exception("Cannot add pte to a packed nsd.")
		if page is not None:
			pte = NsdPte(entry, page)
		elif pgid is not None:
			pte = NsdPte(entry, pgid=pgid)
		idx = entry.eid.bucket_hash
		offset = self.ptb_offsets[idx]
		self.page_table.insert(offset, pte)
		self.ptb_offsets[idx+1:] += 1
		return pte

	def pack(self):
		for pte in self.page_table:
			if pte.eid.entry is not None:
				pte.eid.value = pte.eid.entry.eid.value
		super().pack()

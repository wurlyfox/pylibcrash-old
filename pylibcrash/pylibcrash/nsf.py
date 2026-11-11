import sys
sys.path.append('/home/user/src/ctypemap')
from ctypemap.base import Packable

from libcrash import ffi
from pylibcrash.page import Page, TexturePage
from pylibcrash.entry import Eid

# extension methods for Eid class which use Nsf
# done here to avoid circular dependency
def eid_resolve(self, nsf):
	self.entry = nsf.entry(self)
def eid_unresolve(self):
	if self.resolved:
		self.value = self.entry.eid.value
setattr(Eid, 'resolve', eid_resolve)
setattr(Eid, 'unresolve', eid_unresolve)

class Nsf(Packable):
	field_map = {
		# union is True because the below fields alone define the layout
		# of the struct
		# fields defined in the c struct are unioned with these fields
		'$union': True, 
		'compressed_pages': {
			'pack': ('internal', 0)
		},
		'pages': {
			'pack': ('internal', 1)
		}
	}

	def __init__(self, nsd=None):
		self.dir = nsd
		
	def page(self, pgid):
		idx = pgid.value >> 1
		page = self.pages[idx]
		return page
		
	def entry(self, eid, resolve=True):
		if eid.entry:
			return eid.entry
		pte = self.dir.lookup(eid)
		if pte is None:
			return None
		if pte.eid.entry is not None:
			return pte.eid.entry
		entry = self._entry(eid, pte.pgid)
		if entry is None:
			return None
		if resolve:
			pte.eid.entry = entry
		return entry

	def _entry(self, eid, pgid):
		page = self.page(pgid)
		if page.type == 1: # return the TexturePage directly if type 1
			return page
		for entry in page.entries:
			if entry.eid == eid:
				return entry
		return None

	def entry_idx(self, eid, pgid):
		page = self.page(pgid);
		if page.type == 1:
			return 0
		for idx, entry in enumerate(page.entries):
			if entry.eid == eid:
				return idx
		return -1;

	def entries_of_type(self, type):
		entries = []
		for page in self.pages:
			if page.type == 1: 
				if type == 5: entries.append(page)
				continue
			for entry in page.entries:
				if entry.type == type:
					entries.append(entry)
		return entries
			
	@classmethod
	def from_cdata(cls, obj, *ext):
		nsf = super().from_cdata(obj, *ext)
		nsf.__dict__['dir'] = ext[0]
		ptr = ffi.cast("uint32_t *", nsf.cdata.data)
		ptr[0] = ffi.cast("uint32_t", ext[0].cptr)
		return nsf
		
	@staticmethod
	def from_entries(entries, nsd):
		nsf = Nsf(nsd)
		for entry in entries:
			nsf.add_entry(entry)
		# nsf.pack()
		return nsf

	def add_entry(self, entry):
		"""
		adds an entry to a page in the nsf 
		(one that would still have free space after packing)
		
		the entry is packed if it is not already
		"""
		if self.dir.lookup(entry.eid) is not None:
			return
		def new_packed_size(page, entry):
			size = page.packed_size + 4 + entry.nbytes
			return size
		if entry.packed == False:
			entry.pack()
		if isinstance(entry, TexturePage): # texture page
			pgid = (len(self.pages) << 1) | 1
			self.pages.append(entry)
			self.dir.pte_new(entry, pgid=pgid)
			return
		# find a page in the nsf with room for the entry
		# i.e. such that the packed size of the page (without 
		# padding) plus the size of the new entry and 4 bytes for 
		# its offset, is less than the fixed allocated size of the
		# page (i.e. 65536 bytes)
		page = next((page for page in self.pages 
		   if new_packed_size(page, entry) < page.fixed_size), None)
		# if none is found then create one and append it to the nsf
		if page is None:
			id = len(self.pages)
			page = Page(id)
			self.pages.append(page)
		# append the entry to the page and create a new pte for it
		page.entries.append(entry)
		self.dir.pte_new(entry, page)
	
	def update_zone_dependencies(self):
		"""
		updates page dependencies for all zone entries
		
		this is a root level method because the page dependencies are 
		page ids, which can only exist after the zone entries have been 
		packed into pages
		"""		
		zones = self.entries_of_type(7)
		for zone in zones:
			pgid_map = {}
			tpages = []
			depends = zone.get_dependencies(self)
			for depend in depends:
				if isinstance(depend, TexturePage):
					tpages.append(depend)
				else:
					pte = self.dir.lookup(zone.eid)
					pgid = pte.pgid
					pgid_map[pgid.value] = True
			tpages = tpages[:8]
			tchunks = list(pgid_map.keys())[:32]
			zone.header['tchunk_count'] = len(tchunks)
			for idx, pgid in enumerate(tchunks):
				zone.header['tchunk'][idx] = pgid
			zone.header['tpage_count'] = len(tpages)
			for idx, tpage in enumerate(tpages):
				zone.header['tpage'][idx] = tpage.eid
				
	def pack(self):
		# update zone dependencies
		self.update_zone_dependencies()
		# entries need to be stored in order of index in the page table
		# in-game eid to entry pointer resolution will otherwise fail
		# (this means that the specified order is not maintained)
		def pte_index(entry):
			idx = self.dir.lookup_idx(entry.eid)
			return idx
		for page in self.pages:
			if page.type == 1: continue
			page.entries.sort(key=pte_index)
		# compress pages and find top N=32
		for page in self.pages:
			if not page.packed: page.pack()
		#compressed_pages = [page.compress() for page in self.pages] 
		#compressed_pages.sort(key=lambda p: p.packed_size)
		#self.compressed_pages.extend(compressed_pages[:32])
		super().pack(self.dir)

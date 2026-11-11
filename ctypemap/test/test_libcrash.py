import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/ctypemap')

from libcrash import ffi, lib
from ctypemap.base import Packable, config, cdata_to_pdata
import numpy as np

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
			'lengths': ('compressed_page_offsets', (5,0)),
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

class Page(Packable):
	# union = _entry_data causes the variable size section to begin 
	# at the offset of the _entry_data field (which includes both 
	# offsets and data)
	field_map = {
		'$union': '_entry_data',
		'$subclass': lambda c: TexturePage if c.type==1 else None,
		'entry_data': {
			'count': 'entry_count',
			'size': '$last_offset',
			'offsets': 'entry_offsets',
			'pointers': 'entries',
			'pack': ('internal', 0)
		}
	}
	
class TexturePage(Page):
	field_map = {}
	
class PageCompressed(Packable):
	field_map = {
		'data': {
			'count': 'length',
			'pack': ('internal', 0)
		}
	}
	
class Entry(Packable):
	field_map = {
		'item_data': {
			'count': 'item_count',
			'size': '$last_offset',
			'offsets': 'item_offsets',
			'pointers': 'items',
			'pack': ('internal', 0)
		}
	}

class NsdLdat(Packable):
	pass
	
class NsdPte(Packable):
	pass

class Eid(Packable):
	def __str__(self):
		string = ffi.new("char[6]")
		lib.eid_str(string, self.cdata)
		return str(ffi.string(string), 'utf-8')
	
class Pgid(Packable):
	pass
	
class Lid(Packable):
	pass

type_map = {
	'nsd': Nsd,
	'nsf': Nsf,
	'page': Page,
	'page_compressed': PageCompressed,
	'entry': Entry,
	'nsd_pte': NsdPte,
	'nsd_ldat': NsdLdat,
	'eid_t': Eid,
	'pgid_t': Pgid,
	'lid_t': Lid
}

def test_interactive():
	global type_map
	with open("S0000009.NSD", "rb") as nsd_file:
		nsd_data = nsd_file.read()
	with open("S0000009.NSF", "rb") as nsf_file:
		nsf_data = nsf_file.read()
	
	config(ffi, type_map)
	nsd = Nsd.from_cbytes(nsd_data)
	nsf = Nsf.from_cbytes(nsf_data, nsd)
	
	return nsd, nsf
	
def test():
	global type_map
	with open("S0000009.NSD", "rb") as nsd_file:
		nsd_data = nsd_file.read()
	with open("S0000009.NSF", "rb") as nsf_file:
		nsf_data = nsf_file.read()
	
	config(ffi, type_map)
	nsd = Nsd.from_cbytes(nsd_data)
	nsf = Nsf.from_cbytes(nsf_data, nsd)
	
	
	nsf.unpack()
	
	entry_dict = {}
	for page in nsf.pages:
		if not page.type == 1:
			for entry in page.entries:
				entry_dict[str(entry.eid)] = entry
				
	entry = entry_dict['a0_9Z']
	#print(entry.dtype)
	
	#entry.unpack()
	
	#new_item = np.array([0,1,2,3,4,5,6,7], dtype=np.uint8)
	#entry.items.append(new_item)
	
	#entry.pack()
	
	page = Page()
	for count in [2,4,6,8]:
		entry = Entry()
		for idx, len in enumerate([16,32,64,128,256,64,32,16][:count]):
			data = np.array([idx]*len, dtype=np.uint8)
			entry.items.append(data)
		entry.pack()
		page.entries.append(entry)
	page.pack()
	
	nsd_new = Nsd()
	nsf_new = Nsf()
	nsf_new.pages.append(page)
	nsd_new.pack()
	nsf_new.pack(nsd_new)
	
	print(nsd_new.dtype)
	print(nsf_new.dtype)
	print(nsd_new.page_count)
	#print(page)

	
	#for item in entry.items:*
	#	print(list(item))
		
	#page = Page()
	#print(page.entries)

	
	# for page in nsf.pages
		# if not page.type == 1:
			# print(f"page {page.pgid}: ")
			# for entry in page.entry_data:
				# print(f"entry {entry.eid}: ")
				# print(f"item count { len(entry.item_data) }")
	# print(type(nsf.pages))

test()
				

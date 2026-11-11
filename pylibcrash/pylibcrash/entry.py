import sys
sys.path.append('/home/user/src/ctypemap')
from ctypemap.base import Packable

from libcrash import ffi, lib

class Eid(Packable):
	@staticmethod
	def none():
		return Eid("NONE!")
		
	def __init__(self, string="NONE!"):
		value = ffi.new("eid_t*")
		bytes = string.encode()
		lib.str_eid(bytes, value)
		self.value = value[0].value
		
	def __str__(self):
		string = ffi.new("char[6]")
		lib.eid_str(string, self.cdata)
		return str(ffi.string(string), 'utf-8')
		
	def __repr__(self):
		if self.resolved:
			entry_type = type(self.entry).__name__
			entry_offset = id(self.entry)
			str = f"{self.entry.eid.__str__()} (bound to {entry_type} at" \
			    + f" offset {entry_offset})"
			return str
		else:
			return self.__str__()
		
	def __eq__(self, other):
		return self.value == other.value
		
	def __hash__(self):
		return int(self.value)
		
	@property
	def bucket_hash(self):
		return (self.value >> 15) & 0xFF
	
	# EIDs can also union with entry pointers in c code
	entry_map = {}	
	@property
	def entry(self):
		if not self.resolved: return None
		return Eid.entry_map[self.value]
	
	@entry.setter
	def entry(self, entry):
		self.value = ffi.cast("uint32_t", entry.cptr)
		Eid.entry_map[self.value] = entry
	
	@property
	def resolved(self):
		if (self.value & 1) == 0 and self.value != 0:
			return True
		return False
	
	
class Entry(Packable):
	magic = 0x100FFFF
	field_map = {
		'$subclass_id': 'type',
		'$constants': ['magic'],
		'item_data': {
			'count': 'item_count',
			'size': '$last_offset',
			'offsets': 'item_offsets',
			'pointers': 'items',
			'pack': ('internal', 0)
		}
	}

	def __init__(self, eid=None):
		super().__init__()
		if eid is None:
			eid = Eid.none()
		elif isinstance(eid, str):
			eid = Eid(eid)
		self.eid = eid
	
	def __hash__(self):
		return hash(self.eid)
		
	def get_dependencies(self, nsf):
		"""
		subclasses should implement as necessary
		"""
		return []

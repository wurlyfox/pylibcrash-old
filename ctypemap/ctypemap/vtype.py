from copy import copy

import numpy as np

"""
helper classes for constructing the dictionary of fields for a new 
numpy dtype
"""

class GType:
	"""
	helper class for constructing the dictionary of fields 
	for a new dtype
	
	- auto/re-calculates field offsets upon insertion
	- allows grouping of fields into contiguous sections
	- allows nesting of gtypes in the field format
	- allows lookup of current calculated offset for a field by name
	- allows calculating the current size of the type
	- the corresponding dtype is accessible as a property
	"""
	def __init__(self, section_count=1):
		self.sections = [[] for _ in range(section_count)]
		self.sizes = [0]*section_count
		
	def append(self, name, format, size, idx=0, offset=None):
		if offset is None:	
			offset = sum(self.sizes[0:idx+1])
		tpl = (name, format, offset)
		self.sections[idx].append(tpl)
		self.sizes[idx] += size
		for section in self.sections[idx+1:]:
			for idx, tpl in enumerate(section):
				lst = list(tpl)
				lst[2] += size
				section[idx] = tuple(lst)

	def get_offset(self, name):
		for section in self.sections:
			for tpl in section:
				if tpl[0] == name:
					return tpl[2]
		return None
		
	@property
	def size(self):
		return sum(self.sizes)
		
	@property
	def dtype(self):
		names = []
		formats = []
		offsets = []
		for section in self.sections:
			for tpl in section:
				name, format, offset = tpl
				if isinstance(format, GType):
					format = format.dtype
				names.append(name)
				formats.append(format)
				offsets.append(offset)
		dtype_dict = dict(names=names, formats=formats, offsets=offsets)
		dtype_dict['itemsize'] = self.size
		dtype = np.dtype(dtype_dict)
		return dtype
		
# elif isinstance(format, tuple) and isinstance(format[0], VType):
#	format[0] = format[0].dtype
		
		
class VType(GType):
	"""
	extension of the helper class for constructing the dictionary
	of fields for a new dtype
	
	- explicitly defines the first section as a 'fixed size' section;
	  offset can be specified for fields appended to this section, which
	  will override the auto-calculated offset 
	  (fields in the c structure should map directly to this section)
	  the size of this section can also be set manually
	- defines the remaining sections as contributing to the 
	  'variable size' part of the type; appending of fields to these
	  sections is done normally
	- can wrap a pre-computed dtype; simplifies representation of all 
	  format fields as vtype  
	- variable size part can be enabled to 'overlap' the fixed size 
	  section with the use of a 'union field'
	"""
	def __init__(self, var_count=0):
		super().__init__(1+var_count)
		self.union_field = None
	
	@staticmethod
	def copy(vtype):
		vtype_new = VType(var_count=len(vtype.sections)-1)
		vtype_new.sections = [copy(sect) for sect in vtype.sections]
		vtype_new.fixed_size = vtype.fixed_size
		vtype_new.union_field = vtype.union_field
		return vtype_new
		
	@staticmethod
	def from_dtype(dtype):
		vtype = VType()
		vtype.sections = dtype
		vtype.fixed_size = dtype.itemsize
		return vtype		
	
	@property
	def fixed_size(self):
		return self.sizes[0]
		
	@fixed_size.setter
	def fixed_size(self, fixed_size):
		self.sizes[0] = fixed_size
	
	@property
	def var_size(self):
		return sum(self.sizes[1:])
	
	@property
	def size(self):
		if self.union_field:	
			size = max(self.fixed_size, self.var_offset + self.var_size)
		else:
			size = sum(self.sizes)
		return size
	
	@property
	def var_offset(self):
		if self.union_field == True:
			var_offset = 0
		elif isinstance(self.union_field, str):
			var_offset = self.get_offset(self.union_field) or 0
		else:
			var_offset = self.sizes[0]
		return var_offset
			
	@property
	def is_dtype(self):
		if isinstance(self.sections, np.dtype):
			return True
		if isinstance(self.sections, type) \
		and hasattr(self.sections, 'dtype'):
			return True
		return False
				
	def append(self, name, format, size, idx=0):
		if idx == 0:
			return super().append(name, format, size, 0)
		offset = self.var_offset + sum(self.sizes[1:idx+1])
		return super().append(name, format, size, idx, offset)
	
	def append_to_fixed(self, name, format, offset, size=None):
		if not self.is_dtype:
			tpl = (name, format, offset)
			self.sections[0].append(tpl)
			self.sizes[0] = max(offset, self.sizes[0] + (size if size else 0))
		else:
			raise Exception("cannot append to a dtype vtype")
			
	def append_to_var(self, name, format, size, idx):
		if not self.is_dtype:
			self.append(name, format, size, idx+1)
		else:
			raise Exception("cannot append to a dtype vtype")
	
	@property
	def dtype(self):
		if self.is_dtype: 
			return self.sections
		return super().dtype
		
	def __str__(self):
		try:
			vtype_desc = self.dtype
		except:
			vtype_desc = self.sections
		str = f"VType: {vtype_desc}"
		return str

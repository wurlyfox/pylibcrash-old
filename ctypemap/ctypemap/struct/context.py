from ctypemap.vtype import VType
from ctypemap.struct.info import StructInfo, FieldInfo, ctype_to_ptype

from ctypemap.bitfield import Bitfield
from ctypemap.util import generic
import ctypemap.config as config

import numpy as np

"""
VStructContext requires mapping functionality to be present in the config; 
that is, to build/extend the vtype for the variable size section of a 
structure requires the ability to map all child fields in that section.

VStructContext is of course to be part of the mapping functionality 
itself, but it shouldn't care about that. 

config.map should be set to a function which maps its ctype argument, 
and optional object and allocated size, to a vtype
"""

class VStructContext:
	"""
	includes the logic for building the variable-sized/extended section
	for a vtype
	
	build_offsets - append array of count uint32 for each varsize_offsets meta field
	build_data    - build var or fix data for each internal meta field
	  build_vardata - build and append vararray2d if pointed prim else vararraystructs
	    get_offsets - get offsets from obj; varfmt = varsize, else fixsize
	      get_offsets_varsize - offset of offsets and point to them
	      get_offsets_fixsize - no offsets; compute for fixed size structs
	    build_vtype
	      build_vararray_structs - append data/ctype from pointed to for each
	      build_vararray_2d - append prim array data from pointed to for each
	  build_fixdata
	"""
	def __init__(self, vtype, info, cobj, *ext, res, asize):
		self.vtype = vtype
		self.info = info
		self.cobj = cobj
		self.ext = ext
		self.res = res
		self.asize = asize
		
	@staticmethod
	def _parse_offs_prop(offs_field, prop_name):
		if offs_field.props is None:
			return None, None
		offs_prop = offs_field.props.get(prop_name)
		bits = None
		if isinstance(offs_prop, tuple):
			name, bits = offs_prop
		else:
			name = offs_prop
		return name, bits
		
	@staticmethod
	def parse_offset_prop(offs_field):
		return VStructContext._parse_offs_prop(offs_field, 'offset')
		
	@staticmethod
	def parse_offsets_prop(offs_field):
		return VStructContext._parse_offs_prop(offs_field, 'offsets')
	
	def get_obj(self, field):
		if field.is_external:
			idx = field.props['pack'][1]
			return self.ext[idx]
		return self.cobj
		
	def build_offsets(self):
		"""
		builds the offsets section for the vtype
		each field marked with offsets in the metadata is given its own
		array of offsets, and each offsets array is packed contiguously
		at the end of the struct
		this does not include offsets fields which are a fixed size
		array contained within the c struct; these fields are instead 
		added when building the fixed section of the vtype
		"""
		offsets_fields = [field for field in self.info.meta_fields.values()
						  if field.is_varsize_offsets]
		for field in offsets_fields:
			count = field.get_count(self.get_obj(field), self.asize)
			size_field = field.props.get('size')
			if size_field == '$last_offset': count += 1
			name, _ = self.parse_offsets_prop(field)
			format = np.dtype((np.dtype('uint32'), (count,)))
			size = 4*count
			self.vtype.append_to_var(name, format, size, 0)		
	
	def build_data(self):
		"""
		builds the data section for the vtype
		each field with internal packing is given its own array of data,
		and each data array is packed contiguously at the end of the 
		struct (after the offsets section)
		- if the layout/format varies per struct (or struct in an array of
		struct), then a separate vtype must be generated for each (this
		is the responsibility of build_vardata). 
		- otherwise an array of such struct can be represented by an 
		array vtype with all items the same (fixed format) vtype (this
		is what build_fixdata does)
		"""
		data_fields = [field for field in self.info.meta_fields.values()
					   if field.is_internal]
		for field in data_fields:
			if self.info.is_varfmt_field(field.name):
				self.build_vardata(field)
			else:
				self.build_fixdata(field)	
	
	def get_offset(self, field):
		"""
		retrieves the offset for the given field from the parent object
		attached to it
		the field is overridden by its external field if such field
		exists-that is, the offset for the external field is retrieved
		instead and from its attached object
		"""
		offs_field = self.info.xfields.get(field.name)
		offs_obj = self.get_obj(offs_field)
		offset_field, _ = self.parse_offset_prop(offs_field)
		if offset_field is None:
			var_end = self.vtype.var_offset + self.vtype.var_size
			unitsize = offs_field.props.get("unitsize", 1)
			offset = var_end // unitsize
		else:
			offset_field, bits = self.parse_offset_prop(offs_field)
			offset = getattr(offs_obj, offset_field)
			if self.res:
				base = ffi.addressof(self.cobj)
				offset -= base
			elif bits:
				bitfield = Bitfield(np.uint32, {'offset': bits}, offset)
				offset = bitfield.offset
		return offset
			
	def get_offsets(self, field):
		"""
		retrieves the offsets for the given field from the parent object 
		attached to it
		the field is overridden by its external field if such field
		exists-that is, the offsets for the external field are retrieved
		instead and from its attached object
		"""
		offs_field = self.info.xfields.get(field.name)
		offsets_field, _ = self.parse_offsets_prop(offs_field)
		if offsets_field is None:
			if not offs_field.props.get('varfmt') is True:
				offsets, count = self.compute_offsets(field, offs_field)
				return offsets, count
			offsets = self.get_offsets_fixsize(field, offs_field)
		else:
			offsets = self.get_offsets_varsize(field, offs_field)
		return offsets, None
		
	def get_offsets_varsize(self, field, offs_field):
		offsets_field, bits = self.parse_offsets_prop(offs_field)
		offs_obj = self.get_obj(offs_field)
		if offs_field.is_internal:
			offsets_offset = self.vtype.var_offset if offsets_field == True \
				else self.vtype.get_offset(offsets_field)
		else:
			xdtype = offs_obj.dtype
			offsets_offset = xdtype.fields[offsets_field][1]
			offs_obj = offs_obj.cdata
		
		# get a pointer to the offsets
		ffi = config.ffi
		offs_obj_data = ffi.cast("uint8_t *", ffi.addressof(offs_obj))
		offsets = ffi.cast("uint32_t *", offs_obj_data + offsets_offset)
		if self.res == True:
			count = offs_field.get_count(offs_obj)
			offsets = copy(offsets[0:count])
			base = ffi.addressof(self.cobj)
			for idx in range(len(offsets)):
				offsets[idx] -= base
		elif bits:
			count = offs_field.get_count(offs_obj)
			new_offsets = ffi.new("uint32_t[]", count)
			for idx in range(count):
				value = offsets[idx]
				bitfield = Bitfield(np.uint32, {'offset': bits}, value)
				new_offsets[idx] = bitfield.offset
			offsets = new_offsets
		return offsets
	
	def get_offsets_fixsize(self, field, offs_field):
		ffi = config.ffi
		offs_obj = self.get_obj(offs_field)
		count = offs_field.get_count(offs_obj)
		child_size = ffi.sizeof(offs_field.pointed_type)
		offsets = ffi.new("uint32_t[]", count)
		var_end = self.vtype.var_offset + self.vtype.var_size
		unitsize = offs_field.props.get("unitsize", 1)
		for idx in range(count):
			offsets[idx] = (var_end + (child_size*idx)) // unitsize
		return offsets

	def compute_offsets(self, field, offs_field):
		"""
		if the field's type is varsize struct and no offsets field is
		specified then the offsets must be computed manually, if possible
		
		note that the size property rather than count is used to determine
		the number of structs which fit in the space, and thus the count
		of offsets needed
		"""
		ffi = config.ffi
		obj = self.cobj
		offs_obj = self.get_obj(offs_field)
		obj_data = ffi.cast("uint8_t *", ffi.addressof(obj))
		offsets = []
		unitsize = offs_field.props.get("unitsize", 1)
		child_ctype = offs_field.inferred_type
		offset = self.vtype.var_offset
		size = self.get_last_offset(offs_field, None, None) - offset
		while size > 0:
			child_obj = ffi.cast(child_ctype.cname + " *", 
								 obj_data + offset)[0]
			child_vtype = config.map(child_ctype, child_obj)
			child_size = child_vtype.dtype.itemsize
			offsets.append(offset)
			size -= child_size
			offset += child_size
		count = len(offsets)
		offsets_new = ffi.new("uint32_t[]", count)
		for idx in range(count):
			offsets_new[idx] = offsets[idx]
		count_new = count
		return offsets_new, count_new
					
	def build_vardata(self, field):
		child_obj = self.get_obj(field)
		offs_field = self.info.xfields.get(field.name)
		offs_obj = self.get_obj(offs_field)
		count = offs_field.get_count(offs_obj)
		name = offs_field.pointer_name or field.name
		size_field = offs_field.props.get('size')
		unitsize = offs_field.props.get("unitsize", 1)
		
		offset, offsets = None, None
		is_empty = False
		if count == 0: is_empty = True
		elif count is not None or size_field is not None:
			offsets, count_new = self.get_offsets(field)
			if count_new is not None:
				count = count_new
			if count == 0: is_empty = True
		else:
			offset = self.get_offset(field)
			
		if is_empty:
			format = (np.uint8, (0,))
			self.vtype.append_to_var(name, format, 0, 1)
			return
		if field.partitions is not None:
			self.build_vararray_partitions(offs_field, child_obj,
				offsets, count, unitsize)
			return
		
		# build the [variable dtype] vtype for the data section based on 
		# kind of data indexed
		child_ctype = offs_field.inferred_type
		if count is None:
			child_vtype = self.build_varstruct(offs_field, child_obj,
				offset, unitsize)
		elif child_ctype.kind == 'primitive':
			child_vtype = self.build_vararray_2d(offs_field, child_obj, 
				offsets, count, unitsize)
		else:
			child_vtype = self.build_vararray_structs(offs_field, 
				child_obj, offsets, count, unitsize)
				
		data_offset = offset or offsets[0]
		sect_offset = self.vtype.var_offset + self.vtype.sizes[1]
		pad_size = data_offset - sect_offset
		if not self.vtype.union_field == True and pad_size > 0:
			format = np.dtype((np.dtype('uint8'), (pad_size,)))
			size = pad_size
			self.vtype.append_to_var("padding", format, size, 1)
		
		format = child_vtype
		size = child_vtype.dtype.itemsize
		self.vtype.append_to_var(name, format, size, 1)		
	
	def build_fixdata(self, field):
		ffi = config.ffi
		offs_obj = self.get_obj(field)
		field_count = field.get_count(offs_obj, self.asize)
		name = field.name
		type = field.inferred_type
		count = field_count if field_count is not None else 1
		size = count * ffi.sizeof(type)
		if type.kind == 'primitive':
			ptype = config.map(type, None).dtype
		else:
			ptype = ctype_to_ptype(type)
		if field_count is not None: format = (ptype, (count,))
		else: format = ptype
		self.vtype.append_to_var(name, format, size, 1)
		
	def build_varstruct(self, field, obj, offset, unitsize=1, last_offset=None):
		ffi = config.ffi
		ctype = field.inferred_type
		obj_data = ffi.cast("uint8_t *", ffi.addressof(obj))
		if last_offset is None:
			last_offset = self.get_last_offset(field, None, None)
		size = last_offset - offset
		child_obj = ffi.cast(ctype.cname + " *",
							 obj_data + offset)[0]
		vtype = config.map(ctype, child_obj, asize=size)
		ptype = ctype_to_ptype(ctype, child_obj)
		if ptype:
			dtype = vtype.dtype
			vtype = generic(ptype, dtype)
		return vtype
		
	# NOTE: size must be determined by the difference in successive 
	# offsets and not the 'size' established for the actual child object
	# (or from the [fixed] struct size if forced varfmt)
	# there may be padding between successive objects. 
	# the offset for the next field appended to the vtype is determined 
	# from the current vtype size, which is then accumulated with the 
	# provided 'size'; therefore such size must account for the size of
	# the actual child object PLUS any additional padding following it
	# for the offset to be correct. such size is exactly the difference 
	# between next and current offset (or struct size if fixed)		
	def build_vararray_structs(self, field, obj, offsets, count, unitsize=1, last_offset=None):
		ffi = config.ffi
		ctype = field.inferred_type
		vtype = VType()
		obj_data = ffi.cast("uint8_t *", ffi.addressof(obj))
		if last_offset is not None:
			pass
		elif field.props.get('varfmt') == True:
			size = ffi.sizeof(ctype)
		else:
			last_offset = self.get_last_offset(field, offsets, count)
		for idx in range(count):
			offset = offsets[idx] * unitsize
			# size = format.size
			if last_offset is not None:
				next_offset = last_offset if idx==count-1 \
						 else offsets[idx+1]
				size = (next_offset - offsets[idx]) * unitsize
			child_obj = ffi.cast(ctype.cname + " *", 
								 obj_data + offset)[0]
			format = config.map(ctype, child_obj, asize=size)
			if format.size > size:
				# sometimes 
				vtype.append('i'+str(idx), (np.uint8, size), size, 0)
				continue
			ptype = ctype_to_ptype(ctype, child_obj)
			if ptype:
				dtype = format.dtype
				format = generic(ptype, dtype)
			vtype.append('f'+str(idx), format, size, 0)
		return vtype
			
	def build_vararray_2d(self, field, obj, offsets, count, unitsize=1, last_offset=None):
		ffi = config.ffi
		ctype = field.pointed_type
		vtype = VType()
		if last_offset is None:
			last_offset = self.get_last_offset(field, offsets, count)
		child_vtype = config.map(ctype)
		child_dtype = child_vtype.dtype
		for idx in range(count):
			if idx == count-1:
				next_offset = last_offset
			else:
				next_offset = offsets[idx+1]
			size = (next_offset - offsets[idx]) * unitsize
			len = size // ffi.sizeof(ctype)
			format = (child_dtype, (len,))
			vtype.append('f'+str(idx), format, size, 0)
		return vtype
	
	# for now, non-recursive; only one level of partitioning allowed
	def build_vararray_partitions(self, field, obj, offsets, count, unitsize):
		if field.partitions is None:
			raise Exception("not a partitions field")
		# if last_offset is not None:
			# pass
		# elif field.props.get('varfmt') == True:
			# size = ffi.sizeof(ctype)
		# else:
		last_offset = self.get_last_offset(field, offsets, count)
		start = 0
		for partition in field.partitions:
			pcount = partition.get_count(obj)
			end = start + (pcount or 1)
			poffsets = offsets[start:end]
			plast_offset = offsets[end] if end < count else last_offset
			start += (pcount or 1)
			
			if pcount is None and isinstance(partition.props.get('type'), dict):
				props = partition.props.get('type')
				sub_part = FieldInfo(partition.parent_type, partition.name, props)
				self.build_fixdata(sub_part)
				continue
			
			child_ctype = partition.inferred_type
			if pcount is None:
				child_vtype = self.build_varstruct(partition, obj,
					poffsets[0], unitsize, plast_offset)
			elif child_ctype.kind == 'primitive':
				child_vtype = self.build_vararray_2d(partition, obj, 
					poffsets, pcount, unitsize, plast_offset)
			else:
				child_vtype = self.build_vararray_structs(partition, obj,
					poffsets, pcount, unitsize, plast_offset)
				
			name = partition.name
			format = child_vtype
			size = child_vtype.dtype.itemsize
			self.vtype.append_to_var(name, format, size, 1)
						
	def get_first_offset(self, field, offsets):
		return offsets[0]
		
	def get_last_offset(self, field, offsets, count):
		obj = self.get_obj(field)
		obj_size = field.get_size(obj, asize=self.asize)
		if obj_size == -1: # last_offset
			obj_size = offsets[count]
		elif obj_size is None:
			raise Exception("The size of constituent data for field " + 
				field.name + " cannot be determined. Specify a size " +
				"property for this field.")
		return obj_size
	
	def __str__(self):
		str = f"VStructContext: {{vtype: {self.vtype}, info: {self.info}, " \
			+ f"ext: {self.ext}}}"
		return str

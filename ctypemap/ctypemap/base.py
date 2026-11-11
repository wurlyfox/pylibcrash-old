"""
"""
import numpy as np
from collections import OrderedDict
from copy import copy, deepcopy

from ctypemap.vtype import VType
from ctypemap.bitfield import Bitfield
from ctypemap.util import *
from ctypemap.struct.info import ctype_to_info, ctype_to_ptype, FieldInfo
from ctypemap.struct.context import VStructContext

import ctypemap.config

def config(ffi, type_map):
	ctypemap.config.ffi = ffi
	ctypemap.config.type_map = type_map
	ctypemap.config.map = ctype_to_vtype
	for cname, ptype in type_map.items():
		ctype = ffi.typeof(cname)
		ptype.ctype = ctype
	for cname, ptype in type_map.items():
		# pre-determine the dtype for fixed-size structs
		if ctype.kind == 'primitive': continue
		build_fixed_dtype(ptype)
		build_subclass_map(ptype)
		# if hasattr(ptype, 'field_map'):
			# field_map = ptype.field_map
			# field_map = OrderedDict(sorted(field_map.items(), key=sort_props))
			# ptype.field_map = field_map
	for cname, ptype in type_map.items():
		# pre-determine the dtype for fixed-size structs
		if ctype.kind == 'primitive': continue
		build_bitfield_map(ptype)

def build_fixed_dtype(ptype):
	ctype = ptype.ctype
	if ctype is None: return
	info = ctype_to_info(ctype)
	if info.is_fixsize_struct:
		vtype = fixsize_struct_to_vtype(ctype)
		ptype.dtype = vtype.dtype

def build_subclass_map(ptype):
	#if 'subclass_map' not in ptype.__dict__:
	#	ptype.__dict__['subclass_map'] = {}
	ptype.subclass_map = {}
	for cls in ptype.__subclasses__():
		if 'subclass_id' in cls.__dict__:
			ptype.subclass_map[cls.subclass_id] = cls
			build_subclass_map(cls)

def build_bitfield_map(ptype):
	def get_dtype(ptype):
		ctype = ptype.ctype
		if ctype is None: return None
		info = ctype_to_info(ctype)
		if info.is_fixsize_struct: return ptype.dtype
		vtype = fixsize_struct_to_vtype(ctype)
		return vtype.dtype
	ptype.bitfield_map = {}
	dtype = get_dtype(ptype)
	for name, tuple in dtype.fields.items():
		child_dtype = tuple[0]
		child_ptype = child_dtype.type
		if not isinstance(child_ptype, Bitfield) and \
			not child_ptype.__name__ == 'Bitfield': continue
		bitfields = child_ptype.fields
		for child_name in bitfields:
			ptype.bitfield_map[child_name] = name

def ctype_to_vtype(ctype, obj=None, *ext, asize=None):
	"""
	core type mapper function. maps any ctype to a vtype.

	an object of the ctype or external objects are needed when
	mapping a variable format structure type that is dependent on
	the data (i.e. the data describes the shape of the vtype)

	@param ctype - ctype to map
	@param obj - cobj/cdata of the ctype (for varfmt structures)
	@param *ext - external pobjects (for varfmt structures)
	@param asize - optional maximum size for the result vtype
	"""
	def primitive_to_vtype(ctype):
		ffi = ctypemap.config.ffi
		size = ffi.sizeof(ctype)
		if ctype.cname in ['float', 'double', 'long double']:
			dtype = np.dtype('f' + str(size))
		elif ctype.cname == 'char':
			dtype = np.dtype('c')
		elif ctype.cname == '_Bool':
			dtype = np.dtype(np.bool_)
		elif int(ffi.cast(ctype, -1)) == -1:
			dtype = np.dtype('i' + str(size))
		else:
			dtype = np.dtype('u' + str(size))
		return VType.from_dtype(dtype)

	def struct_to_vtype(ctype):
		info = ctype_to_info(ctype, obj)
		if info.is_varsize_struct:
			vtype = varsize_struct_to_vtype(ctype, obj, *ext, asize=asize)
		else:
			vtype = fixsize_struct_to_vtype(ctype, obj)
		return vtype

	def array_to_vtype(ctype):
		shape, _type = get_carray_shape(ctype)
		ptype = ctype_to_ptype(_type)
		if ptype is not None :
			build_fixed_dtype(ptype)
			dtype = np.dtype((ptype, tuple(shape)))
		else:
			item_vtype = ctype_to_vtype(_type, None)
			if item_vtype is None: return None
			dtype = np.dtype((item_vtype.dtype, tuple(shape)))
		vtype = VType.from_dtype(dtype)
		return vtype

	kind_map = {
		'primitive': primitive_to_vtype,
		'struct': struct_to_vtype,
		'array': array_to_vtype
	}
	dtype_fn = kind_map.get(ctype.kind)
	if dtype_fn:
		# print(f"converting type {ctype.cname} to vtype")
		# print(f"kind: {ctype.kind}")
		return dtype_fn(ctype)
	else:
		# raise ValueError('Unhandled kind {}'.format(ctype.kind))
		return None


fixed_vtype_map = {}
def fixsize_struct_to_vtype(ctype, obj=None):
	info = ctype_to_info(ctype, obj)
	# print(info.ptype.__name__)
	if info.ptype is None:
		raise Exception(f"'{ctype.cname}' is not mapped to a ptype!")
	ptype_name = info.ptype.__name__
	if ptype_name in fixed_vtype_map:
		vtype = VType.copy(fixed_vtype_map[ptype_name])
		return vtype
	vtype = VType(2) # for now
	if info.union_field: vtype.union_field = info.union_field
	# only include fields in the fixsize section (in case struct is not
	# entirely fixsize)
	# note that varsize fields include any offsets/data field pair such
	# that data is varsize, so non-varsize fields will exclude such
	# offsets even if they are part of the fixed section of the struct
	# so we need to explicitly include said fixsize offsets fields
	fields = [field for field in info.c_fields.values() \
		if not field.is_varsize or field.is_fixsize_offsets]
	for field in fields:
		if not field.bitsize == -1:
			continue
		type_name = field.type.cname
		type_map = ctypemap.config.type_map
		# if there is a mapping of ctype to a custom py type
		if type_name in type_map:
			format = VType.from_dtype(type_map[type_name]) # type must have a dtype property
		# else get the standard dtype (likely primitive)
		else:
			# if the type is cached then won't this be inconistent??
			child_obj = field.get_value(obj)
			format = ctype_to_vtype(field.type, child_obj)
			if format is None: continue
		vtype.append_to_fixed(field.name, format, field.offset)
	build_bitfields(fields, vtype)
	set_vtype_fixed_size(ctype, obj, vtype)
	fixed_vtype_map[ptype_name] = vtype
	return VType.copy(vtype)

def varsize_struct_to_vtype(ctype, obj, *ext,
							asize=None, res=False, skip_data=False):
	# create vtype with the fixed section populated
	vtype = fixsize_struct_to_vtype(ctype, obj)
	# create a context for building sections of the varsize struct type
	info = ctype_to_info(ctype, obj)
	context = VStructContext(vtype, info, obj, *ext, res=res, asize=asize)
	# build the offsets section first
	context.build_offsets()
	if skip_data: return vtype
	# now the data section
	context.build_data()
	# return the vtype
	return vtype

def build_bitfields(fields, vtype):
	bitfield_map = {}
	bitfields = [field for field in fields if not field.bitsize == -1]
	for field in bitfields:
		if field.offset not in bitfield_map:
			bitfield_map[field.offset] = []
		bitfield_map[field.offset].append(field)
	for offset, fields in bitfield_map.items():
		ctype = fields[0].type
		bits_tuple = lambda f: (f.bitshift+f.bitsize-1, f.bitshift)
		fields = {field.name: bits_tuple(field) for field in fields}
		name = f'b{offset}'
		dtype = ctype_to_vtype(ctype).dtype
		format = Bitfield.generic(dtype, fields)
		vtype.append_to_fixed(name, format, offset)

def set_vtype_fixed_size(ctype, obj, vtype):
	def is_last_varstruct(field, vtype):
		if field.type.kind == 'array' or not field.is_varstruct:
			return False
		end_offset = field.offset + ffi.sizeof(field.type)
		if end_offset == vtype.fixed_size:
			return True
		return False
	ffi = ctypemap.config.ffi
	vtype.fixed_size = ffi.sizeof(ctype)
	info = ctype_to_info(ctype, obj)
	# a variable sized struct at the end of the c structure will be
	# included in the fixed structure size, but it should be excluded
	last_fields = [field for field in info.c_fields.values()
	               if is_last_varstruct(field, vtype)]
	if len(last_fields) > 0:
		max_size = max([ffi.sizeof(field.type) for field in last_fields])
		vtype.fixed_size -= max_size
	if hasattr(info.ptype, 'field_map') and '$fixed_size' in info.ptype.field_map:
		vtype.fixed_size = info.ptype.field_map['$fixed_size']

def cdata_to_pdata(obj, *ext):
	return Packable.from_cdata(obj, *ext)


class PackedList(list):
	def __init__(self, values):
		super().__init__(values)
		self.packed = np.array(values)

	@property
	def bytes(self):
		bytes = self.packed.view(dtype=np.uint8)
		return bytes

	@property
	def cptr(self):
		cptr = array_to_cptr(self.packed)
		return cptr

	@property
	def itemsize(self):
		itemsize = len(self.bytes)
		return itemsize

class OffsetsPacker:
	"""
	context for packing offsets for a varcount data field containing the
	given list of items
	"""
	def __init__(self, field, items, offset, obj, offs_obj, resolved=True):
		self.field = field
		self.items = items
		self.offset = offset
		self.obj = obj
		self.offs_obj = offs_obj
		self.resolved = resolved
		self.offsets = None

	def offsets_to_bitfields(self):
		# offsets already scaled by unitsize but not item lengths
		unitsize = self.field.props.get('unitsize', 1)
		offsets_field = self.field.props.get('offsets')
		sizes_field = self.field.props.get('sizes')
		bits = offsets_field[1]
		fields = {'offset': bits}
		# should be a tuple
		if sizes_field is not None:
			if not isinstance(sizes_field, tuple) or \
					not sizes_field[0] == offsets_field[0]:
				raise Exception("not implemented")
			size_bits = sizes_field[1]
			fields['size'] = size_bits
		bitfields = [Bitfield(np.uint32, fields) for _ in self.offsets]
		for offset, bitfield, item in zip(self.offsets, bitfields, self.items):
			bitfield.offset = offset
			if sizes_field is not None:
				bitfield.size = item.packed_size // unitsize
		# not really defined what to do for $last_offset when offset
		# s are bitfields. store it anyways
		bitfields[-1].offset = self.offsets[-1]
		self.offsets = np.array([bitfield.value for bitfield in bitfields],
			dtype=np.uint32)
		return self.offsets

	def get_offsets(self):
		"""
		calculates offsets for the attached array of items

		or, if the object has been resolved, simply sets offsets to an
		array of pointers to the items
		"""
		unitsize = self.field.props.get('unitsize', 1)
		for idx, item in enumerate(self.items):
			if isinstance(item, list):
				self.items[idx] = PackedList(item)
		items_bytes = Packer.get_items_bytes(self.items, self.field)
		if self.resolved == False:
			ends = np.cumsum([len(bytes) for bytes in items_bytes],
							  dtype=np.uint32)
			offset = np.array([self.offset], dtype=np.uint32)
			offsets = np.concatenate([offset, ends+self.offset])
			# only this set of offsets scaled down by unitsize
			# note that size is also scaled down as a result
			self.offsets = offsets // unitsize
			count = len(self.items)
			if count > 0:
				self.offset += ends[-1]
		else:
			ffi = ctypemap.config.ffi
			pointers = [int(ffi.cast("uint32_t", item.cptr))
						for item in self.items]
			if self.field.props.get('size') == '$last_offset':
				# the last pointer should not be used when the struct
				# is unpacked or child items are unpacked; it is only
				# relevant when the data items themselves are packed
				# and contiguous; try to calculate it anyways, the space
				# should be filled
				last_pointer = pointers[-1] + self.items[-1].itemsize
				pointers.append(last_pointer)
			self.offsets = np.array(pointers, dtype=np.uint32)
			# assume the pointers are to contiguous locations
			# may not be the case, however, but then the struct is
			# unpacked and resolved in which case only a partial pack is
			# being performed and the offset is irrelevant/unused
			self.offset += sum([len(bytes) for bytes in items_bytes], 0)

	def set_size(self):
		"""
		sets the value of the size field (as specified by metadata) in
		the attached offsets c object

		offsets at this point includes one more value than expected and
		that last offset value is the offset of the last item plus its
		size; this is therefore the total size of the contiguous data
		referenced by the offsets; the value is truncated from the
		offsets and only used to set the size field value UNLESS size
		property specifies that it is to be kept (and used in place of
		a separate size field)

		note that the size is a pointer -only- if is a last offset and
		the object is resolved, in which case it is set along with the
		other offsets as pointers
		"""
		size_field = self.field.props.get('size')
		if not size_field == '$last_offset':
			if size_field is not None:
				if self.resolved:
					items_bytes = Packer.get_items_bytes(self.items, self.field)
					items_size = sum([len(item_bytes) for item_bytes in items_bytes])
					size = self.offset + items_size
				else:
					size = self.offsets[-1]
				self.field.set_size(self.offs_obj, size)
			self.offsets = self.offsets[:-1]

	def set_count(self):
		"""
		sets the count field value in the attached offsets object
		"""
		count = len(self.items)
		self.field.set_count(self.offs_obj, count)

	def parse_offsets_field(self, bitfield_convert=False):
		offsets_field = self.field.props.get('offsets')
		if isinstance(offsets_field, tuple):
			offsets_field = offsets_field[0]
			if bitfield_convert:
				self.offsets = self.offsets_to_bitfields()
		return offsets_field

	def set_offsets(self, xoffsets_out, offsets=None):
		"""
		assigns the offsets that have been calculated by doing one of
		the following:
			- returning the offsets if none of the below are done
			- assigning the offsets to the offsets_field in the attached
			  offsets c object, where offsets_field is specified in
			  metadata, if the field has offsets in the fixed size
			  section of the struct
			- adding the offsets into the xoffsets_out dictionary if it
			  is passed to the function (this takes precedence over all
			  other cases when specified)
            - returning None if the attached field is not an offsets
              field
		"""
		if offsets is not None:
			self.offsets = offsets
			count = len(self.offsets)
		else:
			count = len(self.items)
		packed_offsets = None
		if not self.field.is_offsets:
			return None
		offsets_field = self.parse_offsets_field(offsets is None)
		if not self.offs_obj == self.obj:
			xoffsets_out[self.field.name] = self.offsets
		elif self.field.is_fixsize_offsets:
			obj_offsets = getattr(self.offs_obj.cdata, offsets_field)
			for idx in range(count):
				obj_offsets[idx] = self.offsets[idx]
		else:
			packed_offsets = self.offsets
		return packed_offsets

	def pack(self, xoffsets_out):
		"""
		computes the array of offsets and assigns them to the
		corresponding field in the fixed section OR returns the array
		for packing (concatenating to offsets in the variable section)

		also sets the size and/or count field values in the attached
		offsets c object
		"""
		self.get_offsets()
		self.set_size()
		self.set_count()
		packed_offsets = self.set_offsets(xoffsets_out)
		return packed_offsets

class Packer:

	def __init__(self, obj, *ext, res=False):
		self.obj = obj
		self.ext = ext
		self.info = ctype_to_info(obj.ctype, obj.cdata)
		self.offsets = np.array([], dtype=np.uint32)
		self.vardata = np.array([], dtype=np.uint8)
		self.xoffsets = {}
		self.offset = self.vardata_offset
		self.res = res

	def set_xoffsets(self, xoffsets):
		self.xoffsets = xoffsets

	def get_obj(self, field):
		if field.name in [field.name for field in self.external_fields]:
			idx = field.props['pack'][1]
			return self.ext[idx]
		return self.obj

	@property
	def packed_data_fields(self):
		fields = [self.info.xfields.get(field.name) \
				  for field in self.info.meta_fields.values() \
				  if field.is_internal]
		return fields

	@property
	def packed_offset_fields(self):
		# for now varcount always implies offsets in the var section
		# when the field has offsets
		# UNLESS field implies a fixed size offsets array
		# else if varcount but no offsets, then just a single offset
		# in the c struct, for structs are fixed size
		fields = [self.info.xfields.get(field.name) \
				  for field in self.info.meta_fields.values() \
				  if field.is_offsets and field.is_varcount \
				  and not field.is_fixsize_offsets]
		return fields

	@property
	def fixsize_varcount_fields(self):
		fields = [self.info.xfields.get(field.name) \
				  for field in self.info.meta_fields.values() \
				  if field.is_fixsize_varcount and not field.is_offsets]
		return fields

	@property
	def meta_fields(self):
		fields = [self.info.xfields.get(field.name) \
				  for field in self.info.meta_fields.values()]
		return fields

	@property
	def external_fields(self):
		# external fields ONLY if they are from an external object
		fields = [field
				  for field in self.info.xfields.values()
				  if field not in self.info.meta_fields.values()]
		return fields

	@property
	def packed_offset_count(self):
		offset_count = 0
		for field in self.packed_offset_fields:
			if field in self.xoffsets:
				offset_count += len(self.xoffsets[field])
				continue
			name = field.item_name
			if field.partitions:
				self.merge_partitions(field.partitions, name)
			items = self.obj.unpacked[name]
			offset_count += len(items)
			size_field = field.props.get('size')
			if size_field == '$last_offset':
				offset_count += 1
		return offset_count

	@property
	def packed_offsets_size(self):
		size = self.packed_offset_count * 4
		return size

	@property
	def packed_data_size(self):
		size = 0
		for field in self.packed_data_fields:
			name = field.item_name
			if field.is_varcount:
				if field.partitions:
					self.merge_partitions(field.partitions, name)
				items = self.obj.__getattr__(name)
				if len(items) == 0:
					continue
				size += sum([item.dtype.itemsize for item in items])
			else:
				item = self.obj.__getattr__(name)
				size += item.dtype.itemsize
		return size

	@property
	def packed_size(self):
		# note: does not include padding
		size = self.var_offset + \
			   self.packed_offsets_size + \
			   self.packed_data_size
		return size

	@property
	def fixed_size(self):
		ffi = ctypemap.config.ffi
		size = ffi.sizeof(self.obj.ctype)
		# check for fixed size override
		if hasattr(self.info, 'ptype') and \
				hasattr(self.info.ptype, 'field_map') and \
				'$fixed_size' in self.info.ptype.field_map:
			size = self.info.ptype.field_map['$fixed_size']
		return size

	@property
	def var_offset(self):
		ffi = ctypemap.config.ffi
		union_field = self.info.union_field
		if union_field == True:
			var_offset = 0
		elif isinstance(union_field, str):
			var_offset = ffi.offsetof(self.obj.ctype, union_field)
		else:
			var_offset = self.fixed_size
		return var_offset

	@property
	def vardata_offset(self):
		offset = self.var_offset + self.packed_offsets_size
		return offset

	@staticmethod
	def get_items_bytes(items, field):
		"""
		generates a representative list of bytes array for the unpacked
		data field; use np.concatenate to 'pack' the result list into a
		contiguous bytes array

		if items is a singular item or list of primitive, the result
		will be a list with single item the np bytes array for the item
		or primitives

		(the result is kept unpacked in list form for computing offsets)
		"""
		if not field.is_varcount and not field.props.get('size'):
			items_bytes = [items.bytes]
		elif len(items) == 0:
			items_bytes = [np.array([], dtype=np.uint8)]
		elif not field.is_primitive:
			# TODO: find a better way to do this
			for idx, item in enumerate(items):
				if isinstance(item, list) and not isinstance(item, PackedList):
					items[idx] = PackedList(item)
			items_bytes = [item.bytes for item in items]
		else:
			ctype = field.inferred_type
			vtype = ctype_to_vtype(ctype)
			dtype = vtype.dtype
			items_packed = np.array(items, dtype=dtype)
			items_bytes = [items_packed.view(dtype=np.uint8)]
		return items_bytes

	# def get_item_bytes(self):
		# if isinstance(item, PackedList):
			# return item.bytes
		# if isinstance(item, Packable):
			# return item.bytes
		# else:
			# return item

	def merge_partitions(self, partitions, name, obj=None):
		"""
		merges the unpacked lists/items for the given set of partitions
		into a new unpacked list with the given name

		this is necessary for packing fields with partitions because the
		packing operates on the parent field only

		also, if obj is specified the counts for each partition are
		stored in that obj
		"""
		# if name in self.obj.unpacked: return
		merged = []
		for partition in partitions:
			array_field = partition.array_field
			if array_field and partition.is_varcount:
				raise Exception("not supported yet")
			if partition.is_varcount:
				items = self.obj.unpacked[partition.name]
			else:
				items = [self.obj.unpacked[partition.name]]
			if obj is not None:
				if partition.is_varcount:
					count = len(items)
					partition.set_count(obj, count)
				elif array_field and array_field.is_varcount:
					count = len(items[0])
					array_field.set_count(obj, count)
			merged.extend(items)
		self.obj.unpacked[name] = merged

	def build_offsets(self):
		xoffsets_out = {}
		for field in self.meta_fields:
			offs_obj = self.get_obj(field)
			if field.name in self.xoffsets:
				offsets = self.xoffsets[field.name]
				packer = OffsetsPacker(field, None, self.offset,
									   self.obj, offs_obj)
				packed_offsets = packer.set_offsets(xoffsets_out, offsets)
				if packed_offsets:
					self.offsets = \
						np.concatenate([self.offsets, packed_offsets])
				self.offset = packer.offset
				continue
			name = field.item_name
			if name not in self.obj.unpacked \
					and field.partitions is None:
				# this is OK. the object is being packed and for this
				# field it expects external [ly packed] offsets from an
				# external object, but the external object has not been
				# provided. the packing for these fields will be done
				# in a future second pass in which this object is passed
				# as an xarg (and thus this acts as the external object)
				# to the pack method for some other object
				continue
			# field or its partitions are unpacked and it is a
			# variable count array of variable size structure or
			# prim array (i.e. has offsets)
			if field.is_varcount and field.is_offsets:
				if field.partitions:
					self.merge_partitions(field.partitions, name, offs_obj)
				items = self.obj.unpacked[name]
				packer = OffsetsPacker(field, items, self.offset,
									   self.obj, offs_obj, self.res)
				packed_offsets = packer.pack(xoffsets_out)
				if packed_offsets is not None:
					self.offsets = \
						np.concatenate([self.offsets, packed_offsets])
				self.offset = packer.offset
			# field or its partitions is/are unpacked and it is/they are
			# to be packed to the end of the struct, and the field or its
			# partitions together is/are either:
			# - variable count array of fixed size struct
			# - fixed count array of fixed size struct
			# - variable count array of primitive
			# - a single varsize (or fixsize??) struct
			# - variable or fixed count array of variable size structs,
			#   without offsets (offsets are distributed amongst external
			#   objects)
			elif field.is_packed and not field.is_offsets:
				item = self.obj.unpacked[name]
				size_field = field.props.get('size')
				# if self.res and size_field is not None:
				#	pointer = item.cptr
				#	field.set_size(coffs_obj, pointer)
				#	continue
				#item_bytes = Packer.get_items_bytes(item, field)[0]
				#end = len(item_bytes)
				items_bytes = Packer.get_items_bytes(item, field)
				end = sum([len(item_bytes) for item_bytes in items_bytes])
				self.offset += end
				if size_field is not None:
					# for now, size property is acting as the -end-
					# offset rather than an actual size
					unitsize = field.props.get('unitsize', 1)
					offset = self.offset // unitsize
					field.set_size(offs_obj, offset)
				if field.is_varcount:
					count = len(item)
					field.set_count(offs_obj, count)
		return xoffsets_out

	def build_data(self):
		for field in self.packed_data_fields:
			name = field.item_name
			if field.partitions:
				self.merge_partitions(field.partitions, name)
			items = self.obj.unpacked[name]
			items_bytes = Packer.get_items_bytes(items, field)
			vardata = np.concatenate(items_bytes)
			self.vardata = np.concatenate([self.vardata, vardata])

	def set_data_fixsize_varcount(self):
		for field in self.fixsize_varcount_fields:
			name = field.name
			if field.partitions:
				self.merge_partitions(field.partitions, name)
			items = self.obj.unpacked[name]
			for idx, item in enumerate(items):
				self.obj[name][idx] = item
			field.set_count(self.obj, len(items))

	def pack_partial(self, res=True):
		# concatenate the current fixed data section and offsets
		# (typically overridden with pointers) section only
		self.set_data_fixsize_varcount()
		xoffsets = self.build_offsets()
		fixdata = self.obj.bytes[0:self.var_offset]
		offsets_bytes = self.offsets.view(np.uint8)
		data = np.concatenate([fixdata, offsets_bytes], dtype=np.uint8)
		data_size = len(data)

		ffi = ctypemap.config.ffi
		cdata = data.__array_interface__['data'][0]
		cobj = ffi.cast(self.obj.ctype.cname + " *", cdata)[0]
		vtype = varsize_struct_to_vtype(self.obj.ctype, cobj,
									    asize=data_size,
									    res=res, skip_data=True)
		ptype = ctype_to_ptype(self.obj.ctype, cobj)
		dtype = vtype.dtype
		cls = generic(ptype, dtype)
		dtype = np.dtype(cls)
		reset_dtype(self.obj, dtype, data)

		return self.obj

	def pack(self):
		# concatenate the current fixed data section, new calculated
		# offsets, and new vardata section
		self.set_data_fixsize_varcount()
		xoffsets = self.build_offsets()
		self.build_data()
		fixdata = self.obj.bytes[0:self.var_offset]
		offsets_bytes = self.offsets.view(np.uint8)
		vardata = self.vardata
		data = np.concatenate([fixdata, offsets_bytes, vardata], dtype=np.uint8)

		# concatenate additional padding if the actual c struct size
		# is larger than the final concatenated data;
		# (this is usually the case for varsect union types)
		fixed_size = self.fixed_size
		data_size = len(data)
		if fixed_size > data_size:
			pad_size = fixed_size - data_size
			padding = np.zeros(pad_size, dtype=np.uint8)
			data = np.concatenate([data, padding])
			data_size = len(data)

		# unpack/repack external objects with the offsets
		# generated for them
		# (the counts and size have already been updated)
		# we need these to build the dtype for the main struct
		for xobj in self.ext:
			if xobj.packed == True:
				xobj.unpack()
			packer = Packer(xobj)
			packer.set_xoffsets(xoffsets)
			packer.pack()

		# form an appropriate cpointer to the final data and use it
		# to regenerate the (generic) dtype for the pobject/ctype
		ffi = ctypemap.config.ffi
		cdata = data.__array_interface__['data'][0]
		cobj = ffi.cast(self.obj.ctype.cname + " *", cdata)[0]
		vtype = ctype_to_vtype(self.obj.ctype, cobj, *self.ext, asize=data_size)
		ptype = ctype_to_ptype(self.obj.ctype, cobj)
		dtype = vtype.dtype
		cls = generic(ptype, dtype)
		dtype = np.dtype(cls)
		reset_dtype(self.obj, dtype, data)
		# self.obj = new_of_dtype(dtype, data)

		# update the pobject's ptype (class) and set the packed flag
		self.obj.__class__ = ptype
		self.obj.packed = True

		# return the packed object
		return self.obj
		# if len(ret) == 1:
		#	return self.obj
		# else:
		#	return tuple(ret)

class Packable(np.void, object):
	ctype = None
	subclass_map = {}
	def __new__(cls, *args, **kwargs):
		# if len(args) == 0:
		#	return cls.new()
		#else:
		#	obj = args[0]
		#	ext = args[1:]
		#	return cls.from_cdata(obj, *ext)
		return cls.new()

	@classmethod
	def new(cls):
		# todo: restrict r/w access to count/offsets fields when unpacked
		type_map = ctypemap.config.type_map
		ctype = cls.ctype
		vtype = fixsize_struct_to_vtype(ctype)
		dtype = vtype.dtype
		ptype = cls  # type_map.get(ctype.cname)
		cls = generic(ptype, dtype)
		pobj = np.zeros(1, dtype=cls)[0]
		pobj.__class__ = ptype
		cls._init(pobj, packed=False)
		return pobj

	@classmethod
	def from_cdata(cls, obj, *ext, size=None):
		ffi = ctypemap.config.ffi
		ctype = ffi.typeof(obj)
		vtype = ctype_to_vtype(ctype, obj, *ext, asize=size)
		ptype = ctype_to_ptype(ctype, obj)
		dtype = vtype.dtype
		cls = generic(ptype, dtype)
		addr = ffi.addressof(obj)
		pobj = np.frombuffer(ffi.buffer(addr, vtype.size), dtype=cls)[0]
		pobj.__class__ = ptype
		cls._init(pobj, packed=True)
		return pobj

	@staticmethod
	def copy(pobj):
		ctype = pobj.ctype
		dtype = pobj.dtype
		ptype = ctype_to_ptype(ctype, pobj.cdata)
		cls = generic(ptype, dtype)
		bytes = np.copy(pobj.bytes)
		pobj_new = bytes.view(dtype=cls)[0]
		pobj_new.__class__ = ptype
		cls._init(pobj, packed=True)
		return pobj_new

	@classmethod
	def _init(cls, pobj, packed=False):
		"""
		creates and initializes members used for packing/unpacking
		functionality
		"""
		## cls.__init__(pobj)
		pobj.__dict__['packed'] = packed
		pobj.__dict__['unpacked'] = {}
		pobj.__dict__['resolved'] = True
		if packed == False:
			cls._init_unpacked(pobj)
		return pobj

	def _check_inited(self):
		if 'unpacked' not in self.__dict__:
			self.__class__._init(self, True)

	@classmethod
	def _init_unpacked(cls, pobj):
		"""
		creates new unpacked lists/pobjs for each packed field
		"""
		unpacked = pobj.__dict__['unpacked']
		ctype = pobj.ctype
		info = ctype_to_info(ctype, ptype=cls) #pobj.cdata)
		type_map = ctypemap.config.type_map
		fields = [info.xfields.get(field.name) \
		          for field in info.meta_fields.values() \
		          if field.is_internal or field.is_fixsize_varcount]
		fields = sum([field.partitions or [field] for field in fields], [])
		for idx, field in enumerate(fields):
			props = field.props.get('type')
			if isinstance(props, dict):
				fields[idx] = FieldInfo(field.parent_type, field.name, props)
		for field in fields:
			# todo: support for fixed size array of struct
			# behavior would be to create a new list with n of the ptype
			if field.is_varcount or field.props.get('size'):
				name = first_non_none([field.props.get('pointers'),
									   field.props.get('pointer'),
									   field.name])
				unpacked[name] = []
			else:
				name = first_non_none([field.props.get('pointer'),
									   field.name])
				child_ctype = field.inferred_type
				child_ptype = type_map.get(child_ctype.cname)
				unpacked[name] = child_ptype()

	def __init__(self):
		"""
		initialization of fields
		only called when constructing with the constructor
		"""
		self._init_consts()

	def _init_consts(self):
		"""
		initializes any constant-valued fields
		"""
		type_map = ctypemap.config.type_map
		ctype = self.ctype
		ptype = self.__class__
		# get the base ptype and check if it has a field name specified
		# for $subclass_id
		base_ptype = type_map.get(ctype.cname)
		if hasattr(base_ptype, 'field_map') and \
				'$subclass_id' in base_ptype.field_map and \
				isinstance(base_ptype.field_map['$subclass_id'], str) and \
				hasattr(ptype, 'subclass_id'):
			type_field = base_ptype.field_map['$subclass_id']
			type_id = ptype.subclass_id
			setattr(self, type_field, type_id)
		# do the remaining fields
		if hasattr(ptype, 'field_map') and '$constants' in ptype.field_map:
			fields = ptype.field_map['$constants']
			for field in fields:
				value = getattr(ptype, field)
				setattr(self, field, value)

	def __getattr__(self, attr):
		self._check_inited()
		if attr in self.__dict__['unpacked']:
			return self.__dict__['unpacked'][attr]
		elif attr in self.dtype.fields:
			arg0 = self.dtype.fields[attr][0]
			arg1 = self.dtype.fields[attr][1]
			return self.getfield(arg0, arg1)
		elif attr in self.__class__.bitfield_map:
			name = self.__class__.bitfield_map[attr]
			return getattr(self[name], attr)
		else:
			return self.__getattribute__(attr)

	def __setattr__(self, attr, value):
		self._check_inited()
		if attr in self.__dict__['unpacked']:
			self.__dict__['unpacked'][attr] = value
		elif attr in self.dtype.fields:
			arg0 = self.dtype.fields[attr][0]
			arg1 = self.dtype.fields[attr][1]
			self.setfield(value, arg0, arg1)
		elif attr in self.__class__.bitfield_map:
			name = self.__class__.bitfield_map[attr]
			setattr(self[name], attr, value)
		else:
			super().__setattr__(attr, value)

	def __hasattr__(self, attr):
		self._check_inited()
		if attr in self.__dict__['unpacked']:
			return True
		elif attr in self.dtype.fields:
			return True
		elif attr in self.__class__.bitfield_map:
			return True
		else:
			return super().__hasattr__(attr)

	def unpack(self):
		if self.packed == False:
			raise Exception("tried to unpack something that is already unpacked")
		ctype = self.ctype
		info = ctype_to_info(ctype, self.cdata)
		fields = [info.xfields.get(field.name) \
		          for field in info.meta_fields.values() \
		          if field.is_internal or field.is_fixsize_varcount]
		fields = sum([field.partitions or [field] for field in fields], [])
		for idx, field in enumerate(fields):
			props = field.props.get('type')
			if isinstance(props, dict):
				fields[idx] = FieldInfo(field.parent_type, field.name, props)
		for field in fields:
			if field.is_varcount or field.props.get('size'):
				name = first_non_none([field.props.get('pointers'),
									   field.props.get('pointer'),
									   field.name])
				array = self.__getattr__(name)
				if name in self.unpacked:
					self.unpacked[name + "_tmp"] = self.unpacked[name]
				self.unpacked[name] = list(array)
			else:
				# child_ctype = field.pointed_type
				# child_ptype = type_map.get(child_ctype.cname)
				name = first_non_none([field.props.get('pointer'),
									   field.name])
				item = self.__getattr__(name)
				if name in self.unpacked:
					self.unpacked[name + "_tmp"] = self.unpacked[name]
				self.unpacked[name] = Packable.copy(item)
		self.packed = False

	def pack(self, *ext):
		if not hasattr(self, 'field_map'): return # not [un]packable
		# check that the object isnt already packed
		if self.packed == True:
			raise Exception("tried to pack something that is already packed")
		for key, item in self.unpacked.items():
			if isinstance(item, list):
				items = item
				for idx, item in enumerate(items):
					if isinstance(item, Packable) and item.packed == False:
						item.pack()
						# items[idx] = item.pack()
			elif isinstance(item, Packable) and item.packed == False:
				item.pack()
				# self.unpacked[key] = item.pack()
		packer = Packer(self, *ext)
		packer.pack()
		self.unpacked = {}
		# return packer.pack()

	def resolve(self):
		"""
		the default implementation for resolve:
		- converts all relative offsets in the underlying cdata to
		  pointers
		- resolves all child (Packable) objects

		this has no effect on the current dtype (layout) of the
		structure, i.e. Python's view of the data. it is to be used
		when interfacing with c code which expects fields to contain
		pointers instead of offsets (or any other kind of unresolved
		identifier).
		"""
		info = ctype_to_info(self.ctype, self.cdata)
		fields = [field for field in info.meta_fields.values() \
		          if field.is_internal and field.is_offsets]
		for field in fields:
			offsets_field = field.props.get("offsets")
			if isinstance(offsets_field, tuple):
				# not supported yet
				continue
			offsets = getattr(self, offsets_field)
			count = len(offsets)
			base = int(ctypemap.config.ffi.cast("uint32_t", self.cptr))
			for idx in range(count):
				offsets[idx] += base
		fields = [info.xfields.get(field.name) \
		          for field in info.meta_fields.values() \
		          if field.is_internal]
		fields = sum([field.partitions or [field] for field in fields], [])
		for field in fields:
			if field.is_primitive: continue
			name = field.pointer_name or field.name
			if field.is_varcount:
				array = getattr(self, name)
			else:
				array = [getattr(self, name)]
			for item in array:
				if isinstance(item, Packable):
					item.resolve()
		self.resolved = True

	"""
	for the resolve method, such offsets will usually only exist if the
	object has previously been packed and are determined from the object
	when in that packed state. thus it cannot be used on an unpacked
	object, or cannot be used until the object is packed.

	however (as packing can be expensive) it is possible to force said
	offsets to be generated directly as pointers while the object is
	unpacked, without having to pack in the remaining pointed data

	furthermore it is possible to reinterpret the dtype of the
	underlying cdata excluding the vardata section should foreign c code
	modify the pointers section, and to refresh the unpacked data lists
	accordingly

	the slow method is:
	obj.pack()
	obj.resolve()
	foreign call on obj.cdata which modifies pointers section
	obj.unresolve()
	obj.unpack()

	the fast method:
	obj.sync_cdata()
	foreign call on obj.cdata which modifies pointers section
	obj.cdata_sync()
	"""
	def sync_cdata(self):
		# if self.resolved == False or self.packed == True:
		# raise Exception("sync only allowed for unpacked object with \
		#					 offsets resolved to pointers")
		for key, item in self.unpacked.items():
			if isinstance(item, list):
				items = item
				for idx, item in enumerate(items):
					if isinstance(item, Packable) and item.packed == False:
						item.sync_cdata()
			elif isinstance(item, Packable) and item.packed == False:
				item.sync_cdata()
		packer = Packer(self, res=True)
		packer.pack_partial()
		return self

	def cdata_sync(self):
		if self.resolved == False or self.packed == True:
			raise Exception("sync only allowed for unpacked object with \
			                 offsets resolved to pointers")
		# reinterpret the dtype but do not build the vardata section
		# it is not necessary when there are pointers and the structure
		# is unpacked
		ffi = ctypemap.config.ffi
		vtype = varsize_struct_to_vtype(self.ctype, self.cdata,
										res=True, skip_data=True)
		dtype = vtype.dtype
		cls = generic(self.ptype, dtype)
		dtype = np.dtype(cls)
		data = self.view((np.uint8, dtype.itemsize))
		reset_dtype(self, dtype, data)
		self.__class__ = ptype

		fields = [info.xfields.get(field.name) \
		          for field in info.meta_fields.values() \
		          if field.is_internal and (field.is_offsets or field.is_offset)]
		fields = sum([field.partitions or [field] for field in fields], [])
		for field in fields:
			if field.is_varcount:
				name = first_non_none([field.props.get('pointers'),
									   field.props.get('pointer'),
									   field.name])
				ctype = field.inferred_type
				offsets_field = field.props.get('offsets')
				array = self.__getattr__(offsets_field)
				self.unpacked[name] = []
				for address in array:
					obj = ffi.cast(ctype.cname + " *", address)
					ptype = ctype_to_ptype(ctype, obj)
					pobj = child_ptype.from_cdata(obj)
					self.unpacked[name].append(pobj)
			else:
				# child_ctype = field.pointed_type
				# child_ptype = type_map.get(child_ctype.cname)
				name = first_non_none([field.props.get('pointer'),
									   field.name])
				ctype = field.inferred_type
				offset_field = field.props.get('offset')
				item = self.__getattr__(offset_field)
				obj = ffi.cast(ctype.cname + " *", item)
				ptype = ctype_to_ptype(ctype, obj)
				pobj = child_ptype.from_cdata(obj)
				self.unpacked[name] = pobj
		return self

	@property
	def bytes(self):
		size = self.itemsize
		cbytes = self.view((np.uint8, size))
		return cbytes

	@property
	def cptr(self):
		ffi = ctypemap.config.ffi
		ptr = self.__array_interface__['data'][0]
		cname = self.ctype.cname
		cptr = ffi.cast(cname + " *", ptr)
		return cptr

	@property
	def cdata(self):
		cdata = self.cptr[0]
		return cdata

	@property
	def cbytes(self):
		ffi = ctypemap.config.ffi
		cbytes = ffi.cast("uint8_t *", self.cptr)
		return cbytes

	@classmethod
	def from_cbytes(cls, bytes, *ext):
		if cls.ctype is None:
			raise Exception(f"no ctype set for {cls.__name__}")
		ffi = ctypemap.config.ffi
		carray = ffi.from_buffer(bytes)
		cdata = ffi.cast(cls.ctype.cname + " *", carray)[0]
		return cls.from_cdata(cdata, *ext)

	@property
	def fixed_size(self):
		packer = Packer(self)
		return packer.fixed_size

	@property
	def packed_size(self):
		packer = Packer(self)
		return packer.packed_size

	@classmethod
	def extend_field_map(cls):
		if not hasattr(cls, 'field_map'):
			return {}
		field_map = deepcopy(cls.field_map)
		if '$subclass' in field_map:
			field_map.pop('$subclass')
		if '$subclass_id' in field_map:
			field_map.pop('$subclass_id')
		return field_map

def array_to_cptr(array, cname=None):
	ffi = ctypemap.config.ffi
	if len(array) < 1:
		cname = "void *"
	elif cname is not None:
		cname = cname + " *"
	elif isinstance(array[0], Packable):
		cname = array[0].ctype.cname + " *"
	else:
		return None
	cptr = ffi.cast(cname, array.ctypes.data)
	return cptr

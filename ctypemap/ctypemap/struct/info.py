from cached_property import cached_property
from copy import copy

from ctypemap.util import get_carray_shape
import ctypemap.config as config
	
def ctype_to_ptype(ctype, cobj=None):
	"""
	converts a ctype to non-generic ptype
	
	looks up the mapped ptype corresponding to ctype in the type map
	and returns that ptype; 
	
	OR if a cobj is specified and the corresponding ptype specifies a 
	$subclass or $subclass_id option, then the 'alternate' ptype 
	returned from evaluating the function specified in that option on 
	the c object (which should be a subclass of the base type) is 
	returned instead (unless that subclass itself has a $subclass or
	$subclass_id option, in which case the process repeats recursively
	until a final descendant ptype with no such options is reached)
	
	returns the mapped ptype or descendant ptype
	"""
	ptype = config.type_map.get(ctype.cname)
	ptype = ptype_subclass(ptype, cobj)
	return ptype
	
def ptype_subclass(ptype, cobj):
	"""
	retrieves the alternate subclass (ptype) for a ptype/c object 
	
	only for ptypes which define $subclass or $subclass_id options
	"""
	def get_subclass_id(ptype, cobj):
		if not hasattr(ptype, 'subclass_map'): return None
		name_or_fn = ptype.field_map.get('$subclass_id')	
		if name_or_fn is None: return None
		if isinstance(name_or_fn, str):
			return getattr(cobj, name_or_fn)
		else:
			return name_or_fn(cobj)
	if not (cobj and ptype and hasattr(ptype, 'field_map')):
		return ptype
	ptype_new = None
	if '$subclass' in ptype.field_map:
		subclass_fn = ptype.field_map['$subclass']
		ptype_new = subclass_fn(cobj)
	elif '$subclass_id' in ptype.field_map:
		subclass_id = get_subclass_id(ptype, cobj)
		ptype_new = ptype.subclass_map.get(subclass_id, None)
	if ptype_new:
		ptype = ptype_subclass(ptype_new, cobj)
	return ptype

ptype_map = {}

def ctype_to_info(ctype, cobj=None, ptype=None):
	"""
	gets the structure info for [the ptype corresponding to] the 
	specified ctype/cobj
	"""
	if ptype is None:
		ptype = ctype_to_ptype(ctype, cobj)
	if ptype not in ptype_map:
		if hasattr(ptype, 'ctype') and ptype.ctype is not None:
			ctype = ptype.ctype
		info = StructInfo(ctype, ptype)
		ptype_map[ptype] = info
	return ptype_map[ptype]
		
class StructInfo:
	"""
	wrapper for ctype struct (and its ctype fields) with additional 
	functionality
	
	- c_fields    - used to iterate fields in the fixed section
	                or flexible/zero-sized array fields
	- meta_fields - used to iterate fields in the variable section
	- xfields     - needed for now if a full meta field definition is 
	                spread amongst 2 types, to get the remaining 
	                'external' part
	- is_varsize_struct - needed at this level since all fields must be
	                      tested for varsize (or flexible/zero-sized 
	                      array)
	- union_field - retrieves the corresponding option
	"""
	def __init__(self, ctype, ptype):
		self.ctype = ctype
		self.ptype = ptype
		
	@staticmethod
	def get_meta_fields(ctype, ptype):
		fields = {}
		if ptype is None or not hasattr(ptype, 'field_map'):
			return fields
		for name, props in ptype.field_map.items():
			if name[0] == '$': continue
			fields[name] = FieldInfo(ctype, name, props)
		return fields
		
	@cached_property
	def meta_fields(self):
		"""
		returns a dictionary of only the fields with metadata
		(as added to the ptype)
		"""
		fields = StructInfo.get_meta_fields(self.ctype, self.ptype)
		return fields
		
	@cached_property
	def c_fields(self):
		"""
		returns a dictionary of only the fields in the c struct (ctype)
		metadata will also be included with any such field that has 
		metadata in the ptype
		"""
		fields = {}
		prop_fields = self.prop_fields
		for name, field in self.ctype.fields:
			props = None
			prop_field = prop_fields.get(name)
			if prop_field:
				props = prop_field.props
			fields[name] = FieldInfo(self.ctype, name, props)
		return fields
	
	@cached_property
	def prop_fields(self):
		"""
		returns an extended version of meta_fields which allows a field
		to be retrieved by:
		- the field name (as is the case for meta_fields)
		- the specified offsets field name
		- the specified pointers field name
		"""
		prop_names = ["offsets", "pointers"]
		prop_fields = copy(self.meta_fields)
		for field in self.meta_fields.values():
			for prop in prop_names:
				fname = field.props.get(prop)
				if prop == "offsets" and isinstance(fname, tuple):
					fname = fname[0]
				if fname is not None:
					prop_fields[fname] = field
		return prop_fields
		
	@cached_property
	def fields(self):
		"""
		returns a dictionary of both fields in the c struct (ctype) 
		and [possibly new] fields with metadata in the ptype 
		"""
		fields = {**self.meta_fields, **self.c_fields}
		return fields

	@property
	def xfields(self):
		"""
		returns a version of meta_fields in which any fields which have
		a corresponding external field are replaced with that external
		field
		"""
		xfields = copy(self.meta_fields)
		for xcname in config.type_map.keys():
			xctype = config.ffi.typeof(xcname)
			xptype = ctype_to_ptype(xctype)
			meta_fields = StructInfo.get_meta_fields(xctype, xptype)
			ext_fields = [ext_field for ext_field in meta_fields.values() \
						  if ext_field.is_external \
						  and len(ext_field.props['pack']) > 2 \
						  and ext_field.props['pack'][2].__name__ == self.ptype.__name__]
			for ext_field in ext_fields:
				pointers_field = ext_field.props.get("pointers")
				pointer_field = ext_field.props.get("pointer")
				names = [pointers_field, pointer_field, ext_field.name]
				for name in names:
					if name in xfields:
						xfields[name] = ext_field
						break
		return xfields
				
	@cached_property
	def is_varsize_struct(self):
		"""
		structure has a field of variable size as described by metadata
		or a flexible array
		"""
		for name, field in self.meta_fields.items():
			if field.is_packed:
				return True # for now
			if field.is_varsize:
				return True
			if field.type.kind == 'array': # any struct with flexible array is varsize
				shape, _ = get_carray_shape(field.type)
				if len(shape) == 1 and shape[0] is None or shape[0] == 0:
					return True
		return False
		
	@cached_property
	def is_fixsize_struct(self):
		return not self.is_varsize_struct
		
	@cached_property
	def union_field(self):
		"""
		when True, metadata defines the variable-sized section as 
		occupying the same memory region as the entire ctype struct
		when string, metadata defines the variable-sized section as
		beginning at the offset of the field with that name
		else the variable-sized section is separate from the c struct
		"""
		if self.ptype is None or not hasattr(self.ptype, 'field_map'):
			return None
		return self.ptype.field_map.get('$union')
		
	@cached_property
	def is_subclassed(self):
		if self.ptype is None or not hasattr(self.ptype, 'field_map'):
			return None
		return '$subclass' in self.ptype.field_map \
		    or '$subclass_id' in self.ptype.field_map
		
	def is_varfmt_field(self, name):
		"""
		field is either varsize or forced as varfmt
		
		field with offsets is implied as varsize; if the offsets are
		external then we need to discard that field and grab the 
		external field instead (for the internal field only includes 
		pack order and not the count or offsets info);
		a field without offsets is usually fixsize, however some fixsize
		structs can vary in format and therefore a unique vtype/dtype
		must be created for each such struct. therefore we need the
		option to force this behavior for otherwise a constant format 
		will be assumed for such fixsize structs [and therefore only the
		fixed part of the struct will be included in the final vtype]
		"""
		field = self.xfields.get(name)
		is_varfmt = field.is_offsets or field.is_forced_varfmt or \
		            field.is_varstruct or field.is_substruct
		return is_varfmt
		
	def __str__(self):
		str = f"CDataFields: {{ctype: {self.ctype.cname}," \
			+ f"ptype: {self.ptype}, fields: {self.fields}}}"
		return str

class FieldInfo:
	"""
	wrapper for ctype struct field with additional functionality
	
	new functionality includes:
		- attachment of metadata (dictionary) per-field which,
		  collectively, can describe a structure with fields of varying
		  size/length, type, and other aspects which are not acheivable
		  within the layout of a single c structure
		
	[field type] metadata flags, from existence of metadata properties:
	- is_packed
	- is_varcount
	- is_offsets
	- is_internal
	- is_external
	- is_forced_varfmt
	
	combination flags, from metadata flags and c type information:
	- is_varstruct - is struct or array of struct, and varsize struct 
	                 type
	- is_varsize - is packed and varcount (in var section) or a varsize 
	               struct
	- is_fixsize_array - exists in c struct and is a non-flexible, non-
	                     zero-count array
	- is_fixsize_offsets - the field corresponding to the field's 
	                       offsets property is a fixsize array
	- is_varsize_offsets - the field is varcount (and thus so are 
	                       its offsets) and [has] offsets, but are not
	                       fixsize offsets
	                       [fixsize + varcount is a possibility]
	
	c type information and c object attribute get/set:
	  attributes
	  - count - value of the count c field [for varcount fields]
	  - value - value of the field [for fields in c struct]
	  c field properties
	  - type
	  - offset
	  - bitsize
	  packed field properties
	  - [pointed] type
	  - inferred type?? (why separate?)
	    (offset is calculated from the gtype/vtype for packed fields)		
	"""
	def __init__(self, parent_type, name, props):
		"""
		@param parent_type - the ctype for the containing structure
		@param name - name of the field in the structure
		@param props - metadata dictionary for field
		
		"""
		self.parent_type = parent_type
		self.name = name
		self.props = props
			
	@cached_property
	def c_field(self):
		fields_dict = dict(self.parent_type.fields)
		c_field = fields_dict.get(self.name)
		return c_field
	
	@property
	def is_packed(self):
		"""
		returns True if
		field is packed (ie. it has a pack property)
		"""
		if self.props and 'pack' in self.props:
			return True
		return False
	
	@property
	def is_varcount(self):
		"""
		returns True if
		field is an array of 
			- variable size due to variable number of items
			- fixed size, in terms of allocation, but only using a 
			  variable number of items
		"""
		if self.props and 'count' in self.props:
			return True
		return False
	
	@property
	def is_offsets(self):
		"""
		returns True if
		field includes relative offsets for locating the actual array
		elements which collectively constitute its value.
		(implies an array-valued field)
		"""
		if self.props and 'offsets' in self.props:
			return True
		return False
		
	@cached_property
	def is_varsize(self):
		"""
		returns True if
		field is an variable size array due to variable number of items
		and is a non-field in the c-struct (i.e. not fixed size array 
		with variable number of items),
		or is a field of variable sized struct (single or possibly array)
		"""
		if self.is_packed and self.is_varcount:
			return True
		if self.is_varstruct:
			return True
		if self.props and 'size' in self.props:
			return True
		return False
	
	@cached_property
	def is_fixsize(self):
		"""
		negation of is_varsize
		"""
		return not self.is_varsize
	
	@cached_property
	def is_fixsize_array(self):
		"""
		returns True if field is a single-dimensional, non-flexible 
		array of non-zero size, as specified in the c struct
		"""
		if self.c_field is None:
			return False # cant be fixsize if no underlying c field
		child_ctype = self.c_field.type
		if child_ctype.kind == 'array':
			shape, size = get_carray_shape(child_ctype)
			if len(shape) == 1 and shape[0] and shape[0] > 0:
				return True
		return False	  		
							  
	@cached_property
	def is_fixsize_offsets(self):
		"""
		returns True if field implies a fix-sized array of offsets
		"""
		# note: the field itself is NOT what is to be tested for fixsize
		#       array; 
		#       the data usually wont even have a corresponding
		#       field in the c struct because existence of offsets
		#       would imply array of varsize structs or prim arrays
		#       which cannot be represented. so it itself can never be
		#       fixsize
		#       instead the field for the offsets (the name of which is
		#       in this field's properties) is tested
		if self.props is None:
			return False
		offsets_prop = self.props.get('offsets')
		if isinstance(offsets_prop, tuple):
			offsets_field_name, bits = offsets_prop
		else:
			offsets_field_name = offsets_prop
		if offsets_field_name is None:
			return False
		field = FieldInfo(self.parent_type, offsets_field_name, 
						  self.props)
		return field.is_fixsize_array
		
	@cached_property
	def is_varsize_offsets(self):
		"""
		returns True if field implies a variable-sized array of offsets
		"""
		if not self.is_varcount or self.is_fixsize_offsets:
			return False
		return self.is_offsets
		
	@cached_property
	def is_varstruct(self):
		"""
		returns True if
		field is a struct of variable size or an array of struct of 
		variable size
		"""
		# if not self.is_packed_field:
		#	return False
		type = self.inferred_type
		if type is None:
			return False
		if not type.kind == 'struct':
			return False
		fields = ctype_to_info(type)
		if fields.is_varsize_struct:
			return True
		return False
		
	@cached_property
	def is_fixstruct(self):
		return not self.is_varstruct
		
	@cached_property
	def is_substruct(self):
		type = self.inferred_type
		if type is None:
			return False
		if not type.kind == 'struct':
			return False
		fields = ctype_to_info(type)
		if fields.is_subclassed:
			return True

	@property
	def is_internal(self):
		"""
		returns True if
		field implies an internally packed data section
		field has a pack property with first tuple value of 'internal'
		"""
		if not self.is_packed:
			return False
		if self.props['pack'][0] == 'internal':
			return True
		return False
		
	@property
	def is_external(self):
		"""
		returns True if
		field implies an externally packed data section
		field has a pack property with first tuple value of 'external'
		note: the semantics here are confusing. the truthiness of the 
		value indicates that the field is external with respect to some
		-other- type
		"""
		if not self.is_packed:
			return False
		if self.props['pack'][0] == 'external':
			return True
		return False
	
	@property
	def is_forced_varfmt(self):
		"""
		returns True if
		field is (typically fixed size) struct that has been forcibly
		marked as variable format
		"""
		if self.props and self.props.get('varfmt') == True:
			return True
		return False
		
	@property
	def is_primitive(self):
		"""
		returns True if
		field is a field in the c struct type and is of primitive type
		or array of primitive type
		"""
		if self.c_field is None: 
			return False
		type = self.c_field.type
		if type.kind == 'primitive':
			return True
		if type.kind == 'array' and type.item.kind == 'primitive':
			return True
		return False
		
	@property
	def is_fixsize_varcount(self):
		if self.is_fixsize_array and self.is_varcount:
			return True
		return False
		
	@property
	def offset(self):
		if self.c_field is None:
			return None
		return self.c_field.offset
		
	@property
	def bitsize(self):
		if self.c_field is None:
			return None
		return self.c_field.bitsize
		
	@property
	def bitshift(self):
		if self.c_field is None:
			return None
		return self.c_field.bitshift
		
	@property
	def type(self):
		if self.c_field is None:
			return None
		return self.c_field.type
			
	@cached_property
	def pointed_type(self):
		"""
		retrieves corresponding (array pointer removed) ctype for the
		pointers or pointer field (or type field)
		"""
		if self.props is None:
			return None
		if self.parent_type:
			fields = dict(self.parent_type.fields)
		pointers_field = self.props.get('pointers')
		pointer_field = self.props.get('pointer')
		type_name = self.props.get('type')
		if type_name:
			child_ctype = config.ffi.typeof(type_name)
		elif pointers_field and pointers_field in fields:
			child_ctype = fields.get(pointers_field).type.item.item
		elif pointer_field and pointer_field in fields:
			child_ctype = fields.get(pointer_field).type.item
		else:
			child_ctype = None
			#raise Exception("not implemented. need pointer(s) or type \
			#					field for now") # child_ctype = ???
		return child_ctype

	@cached_property
	def inferred_type(self):
		"""
		retrieves ctype for packed structure field, packed array field, 
		or pointed field
		
		by definition, the name for a pointed field is none of the names
		of existing fields in the underlying c structure
		"""
		field = self.c_field
		if field is None:
			type = self.pointed_type
		elif field.type.kind == 'array':
			shape, type = get_carray_shape(field.type)
		elif field.type.kind in ['struct', 'primitive']:
			type = field.type
		else:
			type = None # pointer fields are not directly processed 
		return type
		
	@cached_property
	def pointer_name(self):
		"""
		retrieves name of the referenced pointers or pointer field in
		the properties if any
		"""
		if 'pointers' in self.props:
			name = self.props['pointers']
		elif 'pointer' in self.props:
			name = self.props['pointer']
		else:
			name = None
		return name
		
	@cached_property
	def item_name(self):
		return self.pointer_name or self.name
	
	@cached_property
	def partitions(self):
		"""
		retrieves the partitions specified in the partitions property
		as 'subfields' of the field
		"""
		if 'partitions' not in self.props:
			return None
		partitions_props = self.props['partitions']
		partitions = []
		for name, props in partitions_props.items():
			partition = FieldInfo(self.parent_type, name, props)
			partitions.append(partition)
		return partitions
		
	@cached_property
	def array_field(self):
		"""
		retrieves the fieldinfo for the array types of the element(s) of 
		a partition if the element(s) is/are array type
		"""
		if not 'type' in self.props:
			return None
		if not isinstance(self.props['type'], dict):
			return None
		temp_props = copy(self.props)
		temp_props['elem_count'] = temp_props.get('count', 1)
		array_props = {**temp_props, **self.props['type']}
		field = FieldInfo(self.parent_type, self.name, array_props)	
		return field	
			
	def get_count(self, cobj, asize=None):
		"""
		retrieves the value of the count as specified in the count 
		property from the specified c object
		
		possible values of the count property are:
		  <field_name> - string
		  '$remainder' - string
		  function of c object returning the count
		"""
		if cobj is None: return None
		count_field = self.props.get('count')
		if count_field is None: return None
		if count_field == '$remainder':
			if self.is_varstruct or asize is None:
				raise Exception("for use of $remainder, field must " + \
				"be a flexible array of fixed size struct or primitive")
			size = config.ffi.sizeof(self.inferred_type)
			count = (asize - self.offset) // size
		elif isinstance(count_field, str):	
			count = getattr(cobj, count_field)
		elif isinstance(count_field, tuple):
			getter = count_field[0]
			count = getter(cobj)
		elif callable(count_field):
			getter = count_field
			count = getter(cobj)
		else:
			count = None
		return count
	
	def set_count(self, pobj, count):
		if pobj is None: return
		count_field = self.props.get('count')
		if count_field is None: return
		if count_field == '$remainder': return # handled separately
		if isinstance(count_field, str):
			setattr(pobj, count_field, count)
		elif isinstance(count_field, tuple):
			setter = count_field[1]
			setter(pobj, count)
			
	def get_size(self, cobj, asize=None):
		if cobj is None: return None
		size_field = self.props.get('size')
		if size_field == '$last_offset':
			size = -1
		elif isinstance(size_field, str):
			size = getattr(cobj, size_field)
		elif isinstance(size_field, tuple):
			getter = size_field[0]
			size = getter(cobj)
		elif callable(size_field):
			getter = size_field
			size = getter(cobj)
		elif asize is not None:
			size = asize
		else:
			size = None
		return size
		
	def set_size(self, pobj, size):
		if pobj is None: return
		size_field = self.props.get('size')
		if size_field is None: return
		if size_field == '$last_offset': return # handled separately
		if isinstance(size_field, str):
			setattr(pobj, size_field, size)
		elif isinstance(size_field, tuple):
			setter = size_field[1]
			setter(pobj, size)
			
	def get_value(self, cobj):
		if cobj is None: return None
		if not hasattr(cobj, self.name): return None
		value = getattr(cobj, self.name)
		return value

	def set_value(self, cobj, value):
		if cobj is None: return
		if not hasattr(cobj, self.name): return
		setattr(cobj, self.name, value)
		
	def __str__(self):
		str = f"CDataField: {{name: {self.name}, "\
			+ f"type: {self.type.cname}, offset: {self.offset}, "\
			+ f"pointed type: {self.pointed_type.cname}, "\
			+ f"inferred type: {self.inferred_type.cname}, "\
			+ f"props: {self.props}}}"
		return str

from ctypemap.util import generic

import numpy as np
		
class Value(np.void):
	"""
	numpy structured array type with a single field.
	
	this type is to be created dynamically as a generic type (with the
	'generic' method). the argument to the generic method is the dtype
	to use for the single structure field.
	
	instances of a generic type can also be constructed by calling the
	constructor with:
	- the dtype to use to create the generic type as the first argument
	- the value to populate the single field as the second argument 
	
	this class should be subclassed to add new functionality to numpy
	structured array field values of primitive type 
	"""
	def __new__(cls, *args, **kwargs):
		dtype = cls.dtype_arg(*args) or 0
		value = cls.value_arg(*args) or 0
		ptype = cls.generic(*args, **kwargs)
		value = np.array([value], dtype=ptype)[0]
		return value
		
	@classmethod
	def dtype_arg(cls, *args):
		if len(args) > 0: return args[0]
		return None
		
	@classmethod
	def value_arg(cls, *args):
		if len(args) > 1: return args[1]
		return None
		
	@classmethod
	def base_dtype(cls, *args):
		dtype = args[0]
		dtype = np.dtype([('value', dtype)])
		return dtype
		
	@classmethod
	def generic(cls, *args, **kwargs):
		dtype = cls.base_dtype(*args)
		return generic(cls, dtype)
		
	@property
	def value(self):
		return self['value']
		
	@value.setter
	def value(self, value):
		self['value'] = value

class Bitfield(Value):	
	"""
	numpy structured array type with bitfield get/set functionality
	
	use to support, for example, binding to structured cdata with 
	bitfields
	"""
	@classmethod
	def value_arg(cls, *args):
		if len(args) > 2: return args[2]
		return None
		
	@classmethod
	def generic(cls, *args, **kwargs):
		dtype = cls.base_dtype(*args)
		fields = args[1]
		props = {'fields': fields}
		ptype = generic(cls, dtype, props)
		return ptype
		
	def __getattr__(self, attr):
		if attr.startswith("__"):
			return super().__getattr__(attr)
		elif attr in self.__class__.fields:
			return self.get_field_value(attr)
		else:
			return super().__getattr__(attr)
			
	def __setattr__(self, attr, value):
		if attr.startswith("__"):
			super().__setattr__(attr, value)
		elif attr in self.__class__.fields:
			return self.set_field_value(attr, value)
		else:
			super().__setattr__(attr, value)
			
	def __hasattr__(self, attr):
		if attr.startswith("__"):
			return super().__hasattr__(attr)
		elif attr in self.__class__.fields:
			return True
		else:
			return super().__hasattr__(attr)
			
	@staticmethod	
	def ones(blen):
		return ((2 ** blen) - 1)
		
	def get_field_value(self, field):
		span = self.fields[field]
		shamt = span[1]
		blen = (span[0] - span[1]) + 1
		mask = Bitfield.ones(blen) << shamt
		value = (self.value & mask) >> shamt
		return value
		
	def set_field_value(self, field, value):
		span = self.fields[field]
		flen = self.dtype.itemsize*8
		shamt = span[1]
		mlen_r = shamt
		blen = (span[0] - span[1]) + 1
		shamt_l = blen + mlen_r
		mlen_l = flen - shamt_l
		vmask = Bitfield.ones(blen)
		omask = Bitfield.ones(mlen_r) | (Bitfield.ones(mlen_l) << shamt_l)
		self.value = (self.value & omask) | ((value & vmask) << shamt)
		
	def __str__(self):
		return self.__repr__()
		
	def __repr__(self):
		field_names = list(self.fields.keys())
		values = { name: getattr(self, name) for name in field_names}
		str = f'Bitfield: {{ dtype: {self.dtype}, fields: {self.fields}' \
		    + f', values: {values}, value: {self.value} }}'
		return str

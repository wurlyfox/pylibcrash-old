import numpy as np
import ctypemap.config as config

def generic(cls, dtype, props={}):
	def __new__(_cls, *args, **kwargs):
		obj = _cls(*args, **kwargs)
		obj.__class__ = cls
	name = cls.__name__
	cls = type(name, (cls,np.void), {**{
		'__new__': __new__,
		'dtype': dtype,
	},**props})
	return cls
	
def get_carray_shape(ctype):
	shape = []
	while ctype.kind == 'array':
		shape.append(ctype.length)
		ctype = ctype.item
	return shape, ctype

def value_type_eq(a, b):
	if a == b and type(a) == type(b):
		return True
	return False
	
def sequence(list, terminals=[None], val=0):
	for fn in list:
		val = fn(val)		
#		if val in terminals:
#			return None
		if next((True for v in terminals \
				if value_type_eq(val, v)), False):
			return None
	return val
	
def last_if_all(list):
	if any(True if item is None else False for item in list):
		return None
	return list[-1]
	
def first_non_none(list):
	list = [item for item in list if item is not None]
	if len(list) == 0:
		return None
	return list[0]
	
def reverse_dict(dict):
	return {v: k for k, v in dict.items()}
	
keep_objs = []
	
def reset_dtype(void, dtype, bytes=None):
	# this is a hack to change the dtype of an np.void
	# write access to this property is understandably restricted 
	# however in the case of Packable, it is an structured array which
	# can be unpacked, modified, and repacked, resulting in a change of
	# structure/dtype. 
	ffi = config.ffi
	ptr_cur = ffi.cast("uint32_t *", id(void))
	if bytes is None:
		base_new = np.zeros(1, dtype=dtype)
	else:
		base_new = np.frombuffer(bytes, dtype=dtype)
	void_new = base_new[0]
	keep_objs.append(base_new)
	keep_objs.append(void_new)
	ptr_new = ffi.cast("uint32_t *", id(void_new))
	if bytes is None:	
		data_cur = ffi.cast("uint8_t *", ptr_cur[3])
		data_new = ffi.cast("uint8_t *", ptr_new[3])
		size_cur = void.dtype.itemsize
		size_new = dtype.itemsize
		for idx in range(min(size_cur, size_new)):
			data_new[idx] = data_cur[idx]
			
	base_ptr_new = ffi.cast("uint32_t *", id(base_new))
	base_ptr_cur = ffi.cast("uint32_t *", ptr_cur[6])
	descr_ptr_new = ffi.cast("uint32_t *", ptr_new[4])
	descr_ptr_cur = ffi.cast("uint32_t *", ptr_cur[4])
	# weakref_ptr_cur = ffi.cast("uint32_t *", ptr_cur[8])
	ptr_cur[3] = ptr_new[3]  # change data pointer
	ptr_cur[4] = ptr_new[4]  # change descr pointer
	ptr_cur[6] = ptr_new[6]  # change base pointer
	# ptr_cur[8] = ptr_new[8]  # change weakref pointer
	
	# increment reference counter for base_new
	# and decrement reference counter for base_cur
	# void_new object will be destroyed when the method completes
	# as will base_new after its reference counter is decremented
	# accordingly, -unless- it is incremented prior/made aware that
	# void object now also references it
	base_ptr_cur[0] = base_ptr_cur[0] - 1
	base_ptr_new[0] = base_ptr_new[0] + 1
	descr_ptr_cur[0] = descr_ptr_cur[0] - 1
	descr_ptr_new[0] = descr_ptr_new[0] + 1
	# weakref_ptr_cur[0] = weakref_ptr_cur[0] - 1

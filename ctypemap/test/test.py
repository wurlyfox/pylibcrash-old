import sys
sys.path.append('/home/user/src/ctypemap')

from _test import ffi, lib
from random import seed, randint
import numpy as np

from ctypemap.base import use_type_map, cdata_to_pdata

# field map maps fields to metadata dictionary of properties

class TestStructA(np.void):
	
	# 1) count internal, data internal, no offsets 
	field_map = {
		'items': {
			'count': 'count',
			'pack': ('internal', 0)
		} 
	}

class TestStructB(np.void):
	
	# 2) count internal, data internal, offsets internal
	#    each item is a varcount array of primitive type
	field_map = {
		'item_data': {
			'count': 'count',
			'offsets': 'offsets',
			'pointers': 'items',
			'size': '$last_offset',
			'pack': ('internal', 0)
		}
	}
	
class TestStructC(np.void):
	
	# 3) count internal, data internal, offsets internal
	#    child struct
	
	field_map = {
		'struct_data': {
			'count': 'count',
			'offsets': 'offsets',
			'pointers': 'structs',
			'pack': ('internal', 0)
		}
	}
	
class TestStructD(np.void):
	
	# 4) count internal, data external, offsets internal
	#    child struct
	
	field_map = {
		'structs': {
			'count': 'count',
			'offsets': 'offsets',
			'pointers': 'structs',
			'pack': ('external', 0)
		}
	}

class TsbArray(np.void):
	field_map = {
		'structs': {
			'pack': ('internal', 0)
		}
	}
	
class TestStructE(np.void):
	field_map = {
		'item_data': {
			'count': 'count',
			'offsets': 'offsets',
			'pointers': 'items',
			'size': '$last_offset',
			'pack': ('internal', 0)
		}
	}
	
def mock_tsa(ptr=None):
	if ptr is None:
		ptr = ffi.new("uint8_t[]", 512)	
	tsa = ffi.cast("test_struct_a *", ptr)
	tsa.count = 127
	for idx in range(tsa.count):
		tsa.items[idx] = idx
	return tsa

def mock_tsb_size(count=4):
	size = count*256
	return size
	
def mock_tsb(count=4, ptr=None):
	size = mock_tsb_size(count)
	if ptr is None:
		ptr = ffi.new("uint8_t[]", size)
	tsb = ffi.cast("test_struct_b *", ptr)
	tsb.count = count
	
	offset = (count+2)*4
	for idx in range(count):
		tsb.offsets[idx] = offset
		itemsize = randint(0,count*16)*4
		offset += itemsize
	tsb.offsets[count] = size
	
	for idx in range(count):
		for i in range(tsb.offsets[idx], tsb.offsets[idx+1]):
			ptr[i] = idx+1
	return tsb
	
def mock_tsc_size(count=4):
	size = (count+1)*4 + \
		   sum([mock_tsb_size(idx+4) for idx in range(count)])
	return size
			
def mock_tsc(count=4, ptr=None):
	size = mock_tsc_size(count)
	if ptr is None:
		ptr = ffi.new("uint8_t[]", size)
	tsc = ffi.cast("test_struct_c *", ptr)
	tsc.count = count
	
	offset = (count+1)*4
	for idx in range(count):
		tsc.offsets[idx] = offset
		tsb = mock_tsb(idx+4, ptr+offset)
		offset += tsb.offsets[tsb.count] # adding size of tsb
	
	# don't need a 'size' offset since we can get the size from 
	# last offset + last_size
	return tsc

def mock_tsd_size(count=4):
	size = (count+1)*4
	return size
	
def mock_tsb_array_size(count=4):
	size = 4+sum([mock_tsb_size(idx+4) for idx in range(count)])
	return size
	
def mock_tsd(count=4, ptr=None, ptrb=None):
	size = mock_tsd_size(count)
	varsize = mock_tsb_array_size(count)
	if ptr is None:
		ptr = ffi.new("uint8_t[]", size)
	tsd = ffi.cast("test_struct_d *", ptr)
	tsd.count = count
	
	if ptrb is None:
		ptrb = ffi.new("uint8_t[]", varsize)
	tsdb = ffi.cast("tsb_array *", ptrb)
	tsdb.dummy = 0
	
	offset = 4
	for idx in range(count):
		tsd.offsets[idx] = offset
		tsb = mock_tsb(idx+4, ptrb+offset)
		offset += tsb.offsets[tsb.count]
	
	return tsd, tsdb
	
def mock_tse_size(count=4):
	size = count*256
	return size
	
def mock_tse(count=4, ptr=None):
	size = mock_tse_size(count)
	if ptr is None:
		ptr = ffi.new("uint8_t[]", size)
	tse = ffi.cast("test_struct_e *", ptr)
	tse.count = count
	
	offset = (1+64)*4
	for idx in range(count):
		tse.offsets[idx] = offset
		itemsize = randint(0,count*16)*4
		offset += itemsize
	tse.offsets[count] = size
	
	for idx in range(count):
		for i in range(tse.offsets[idx], tse.offsets[idx+1]):
			ptr[i] = idx+1
	return tse
	
def test():
	seed()
	type_map = {
		"test_struct_a": TestStructA,
		"test_struct_b": TestStructB,
		"test_struct_c": TestStructC,
		"test_struct_d": TestStructD,
		"tsb_array": TsbArray,
		"test_struct_e": TestStructE
	}
	use_type_map(type_map)
	
	# ptr = ffi.new('uint8_t[]', 512)
	# tsa = mock_tsa(ptr=ptr)
	# ptr = ffi.new('uint8_t[]', mock_tsb_size())
	# tsb = mock_tsb(ptr=ptr)
	# ptr = ffi.new('uint8_t[]', mock_tsc_size())
	# tsc = mock_tsc(ptr=ptr)
	ptr = ffi.new("uint8_t[]", mock_tsd_size())
	ptrb = ffi.new("uint8_t[]", mock_tsb_array_size())
	tsd, tsdb = mock_tsd(ptr=ptr, ptrb=ptrb)
	ptr = ffi.new("uint8_t[]", mock_tse_size())
	tse = mock_tse(ptr=ptr)

	# pobja = cdata_to_pdata(ffi, tsa[0])
	# pobjb = cdata_to_pdata(ffi, tsb[0])
	# pobjc = cdata_to_pdata(ffi, tsc[0])
	pobjd = cdata_to_pdata(ffi, tsd[0])
	pobjdb = cdata_to_pdata(ffi, tsdb[0], pobjd)
	pobje = cdata_to_pdata(ffi, tse[0])
	# print(pobja)
	# print(type(pobja))
	# print(pobja.dtype)
	# print(pobjb)
	# print(type(pobjb))
	# print(pobjb.dtype)
	# print(pobjc)
	# print(type(pobjc))
	# print(pobjc.dtype)
	print(pobjd)
	print(type(pobjd))
	print(pobjd.dtype)
	print(pobjdb)
	print(type(pobjdb))
	print(pobjdb.dtype)
	print(pobje)
	print(type(pobje))
	print(pobje.dtype)
	
if __name__ == "__main__":
	test()

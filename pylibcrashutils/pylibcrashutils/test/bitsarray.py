import sys
sys.path.append('/home/user/src/pylibcrashutils')

from pylibcrashutils.general.bitsarray import SimpleBitsArray

from functools import reduce
import numpy as np

"""
Tests for SimpleBitsArray

handle all cases of usage except for exception-causing
"""

#def mock_array(shape):
#	size = np.product(shape)
#	lst = range(size)
#	array = np.array(lst).reshape(shape)
#	return array

def gen_indices(shape, append=[]):
	if len(shape) != 1:
		for idx in range(shape[0]):
			yield from gen_indices(shape[1:], append+[idx])
	else:
		for idx in range(shape[0]):
			yield tuple(append+[idx])
			
def limit_values(values, blen):
	size = 8 // blen
	values = np.array([value & ((1 << blen)-1) for value in values])
	return values

def pack_values(values, blen):
	size = 8 // blen
	packed_values = np.split(values, len(values)//size)
	packed_values = [reduce(lambda a,v: (a << blen) | v, value, 0)
					 for value in packed_values]
	packed_values = np.array(packed_values, dtype=np.uint8)
	return packed_values
		
def test_simple_bits_array_get_value_from_1d():	
	for blen in [4,2,1]:
		values = limit_values(range(32), blen)
		packed_values = pack_values(values, blen)
		array = SimpleBitsArray(packed_values, blen, True)
		for idx in range(32):
			value = array[idx]
			assert value == values[idx]

def test_simple_bits_array_get_value_from_nd():
	for shape_len in range(2,4):
		shape = tuple([32]*shape_len)
		length = np.product(shape)
		for blen in [4,2,1]:
			size = 8 // blen
			values = limit_values(range(length), blen)
			packed_values = pack_values(values, blen)
			packed_shape = tuple(list(shape[:-1]) + [(shape[-1] // size)])
			packed_values = packed_values.reshape(packed_shape)
			array = SimpleBitsArray(packed_values, blen, True)
			values = (value for value in values)
			for idx in gen_indices(shape):
				value = array[idx]
				assert value == next(values)
				
def test_simple_bits_array_get_1d_from_1d():
	for blen in [4,2,1]:
		size = 8 // blen
		values = limit_values(range(32), blen)
		packed_values = pack_values(values, blen)
		array = SimpleBitsArray(packed_values, blen, True)
		for idx in range(0,32,size):
			for length in range(size,32+size,size):
				subarray = array[idx:idx+length]
				for i in range(length-idx):
					assert subarray[i] == values[idx+i]

def test_simple_bits_array_get_nd_from_nd():
	# tests retrieval of all possible subarrays of equal dimension from
	# arrays of increasing dimension for component sizes of 8 and for 
	# each possible bitlength
	
	for shape_len in range(2,4):
		shape = tuple([8]*shape_len)
		length = np.product(shape)
		for blen in [4,2,1]:
			size = 8 // blen
			values = limit_values(range(length), blen)
			packed_values = pack_values(values, blen)
			packed_shape = tuple(list(shape[:-1]) + [(shape[-1] // size)])
			
			values = np.array(values).reshape(shape)
			packed_values = packed_values.reshape(packed_shape)
			
			array = SimpleBitsArray(packed_values, blen, True)
			for start in gen_indices(packed_shape):
				start = tuple(list(start[:-1]) + [(start[-1] * size)])
				for stop in gen_indices(packed_shape):
					stop = tuple(list(stop[:-1]) + [(stop[-1] * size)])
					subshape = tuple([sp-st for st,sp in zip(start, stop)])
					if any(value <= 0 for value in subshape): continue
					idx = tuple([slice(st,sp) for st,sp in zip(start, stop)])
					subarray = array[idx]
					expected = values[idx]
					for idx in gen_indices(subshape):
						assert subarray[idx] == expected[idx]

def test_simple_bits_array_set_value_in_1d():	
	for blen in [4,2,1]:
		values = limit_values(range(32), blen)
		zeros = limit_values([0]*32, blen)
		packed_zeros = pack_values(zeros, blen)
		array = SimpleBitsArray(packed_zeros, blen, True)
		for idx in range(32):
			assert array[idx] == 0
			array[idx] = values[idx]
		for idx in range(32):
			assert array[idx] == values[idx]

def test_simple_bits_array_set_value_in_nd():
	for shape_len in range(2,4):
		shape = tuple([32]*shape_len)
		length = np.product(shape)
		for blen in [4,2,1]:
			size = 8 // blen
			values = limit_values(range(length), blen)
			values = np.array(values).reshape(shape)
			zeros = limit_values([0]*length, blen)
			packed_zeros = pack_values(zeros, blen)
			packed_shape = tuple(list(shape[:-1]) + [(shape[-1] // size)])
			packed_zeros = packed_zeros.reshape(packed_shape)
			array = SimpleBitsArray(packed_zeros, blen, True)
			for idx in gen_indices(shape):
				assert array[idx] == 0
				array[idx] = values[idx]
			for idx in gen_indices(shape):
				assert array[idx] == values[idx]
	
def test_simple_bits_array_set_1d_in_1d():
	for blen in [4,2,1]:
		size = 8 // blen
		zeros = limit_values([0]*32, blen)
		packed_zeros = pack_values(zeros, blen)
		array = SimpleBitsArray(packed_zeros, blen, True)
		for i in range(32):
			assert array[i] == 0
		for idx in range(0,32,size):
			for length in range(size,32+size,size):
				values = np.array(limit_values(range(length), blen))
				print(idx, idx+length)
				array[idx:idx+length] = values
				for i in range(length-idx):
					assert array[idx+i] == values[i]

def test_simple_bits_array_set_nd_in_nd():
	for shape_len in range(2,4):
		shape = tuple([8]*shape_len)
		length = np.product(shape)
		for blen in [4,2,1]:
			size = 8 // blen
			zeros = limit_values([0]*length, blen)
			packed_zeros = pack_values(zeros, blen)
			packed_shape = tuple(list(shape[:-1]) + [(shape[-1] // size)])
			packed_zeros = packed_zeros.reshape(packed_shape)
			array = SimpleBitsArray(packed_zeros, blen, True)
			for idx in gen_indices(shape):
				assert array[idx] == 0
			for start in gen_indices(packed_shape):
				start = tuple(list(start[:-1]) + [(start[-1] * size)])
				for stop in gen_indices(packed_shape):
					stop = tuple(list(stop[:-1]) + [(stop[-1] * size)])
					subshape = tuple([sp-st for st,sp in zip(start, stop)])
					if any(value <= 0 for value in subshape): continue
					idx = tuple([slice(st,sp) for st,sp in zip(start, stop)])
					slength = np.product(subshape)
					values = np.array(limit_values(range(slength), blen))
					values = values.reshape(subshape)
					array[idx] = values # set occurs here
					for idx in gen_indices(subshape):
						aidx = tuple([idx[i]+start[i] 
									for i in range(len(idx))])
						assert array[aidx] == values[idx]

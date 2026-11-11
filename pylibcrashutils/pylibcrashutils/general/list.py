import math
from copy import copy

def new_array(shape, fill_val=None):
	if len(shape) == 0:
		return fill_val
	arr = [new_array(shape[1:]) for i in range(0, shape[0])]
	return arr

def add(a, b):
	res = copy(a)
	for idx, val in enumerate(a):
		res[idx] += b[idx]
	return res

def sub(a, b):
	res = copy(a)
	for idx, val in enumerate(a):
		res[idx] -= b[idx]
	return res

def mul(a, b):
	res = copy(a)
	for idx, val in enumerate(a):
		res[idx] *= b[idx]
	return res

def list_shape(lst, verify=False):
	shape = [len(lst)]
	if shape[0] > 0 and isinstance(lst[0], list):
		subshape = list_shape(lst[0], verify)
		shape.extend(list(subshape))
		if verify == True:
			for item in lst[1:]:
				if not isinstance(item, list) \
						or subshape != list_shape(item, verify):
					raise Exception("jagged list")
	return tuple(shape)
	
def sublist(lst, slices):
	slc = slices[0]
	if not isinstance(slc, slice):
		slc = slice(*slc)
	if len(slices) > 1:
		return [sublist(item, slices[1:]) for item in lst[slc]]
	else:
		return lst[slc]

def flatten(lst):
	res = []
	for item in lst:
		if isinstance(item, list):
			res.extend(flatten(item))
		else:
			res.append(item)
	return res
		
def split_idxs(arr, idxs):
	res = []
	prev_idx = idxs[0]
	for idx in idxs[1:]:
		res.append(arr[prev_idx:idx])
		prev_idx = idx
	res.append(arr[prev_idx:])
	return res

def split_count(arr, group_count):
	# array of length m, divide into n groups, size of n-1 will be floor(m/n)
	# size of last will be floor(m/n) + m%n
	# size s_i can be made closer to the last size by
	# s_i = floor(m/n) + 1
	# s_n = floor(m/n) + m%n - p   (for p x i's)
	group_size = len(arr) // group_count
	
	idxs = [group_size * i for i in range(0, group_count)]
	return split_idxs(arr, idxs)

def split_size(arr, group_size, ceil=True):
	if ceil: group_count = int(math.ceil(len(arr) / group_size))
	else: group_count = len(arr) // group_size
	idxs = [group_size * i for i in range(0, group_count)]
	return split_idxs(arr, idxs)

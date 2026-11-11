import numpy as np
import math

class SimpleBitsArray:
	"""
	Array of bitfields of equal bitlength such that:
	- no field crosses byte-boundaries
	- fields are packed contiguously into bytes and occupy them in their
	  entirety (i.e. no part of any byte is unused)
	- bytes are contiguous in memory
	
	Field bitlength is thus limited to integer powers of 2 less than or 
	equal to 8 (although length 8 would just be a byte array, which is 
	not handled here).
	"""
	# @staticmethod
	# def get_consts(self):
	#	sizes = [2**idx for idx in range(3)]
	#	counts = [8 // size for size in sizes]
	#	shamts = [list(range(8,0,-size)) for size in sizes]
	#	masks = [((1 << size)-1) for size in sizes]
	#	masks = [[mask << shamt for shamt in shamts[idx]] 
	#			 for idx, mask in enumerate(masks)]
	masks = [np.array(arr, dtype=np.uint8) for arr in
	        [[0x80, 0x40, 0x20, 0x10, 0x8, 0x4, 0x2, 0x1],
	         [0xC0, 0x30, 0x0C, 0x03],
	         [0xF0, 0x0F]]]
	shamts = [np.array(arr, dtype=np.uint8) for arr in
	         [[7,6,5,4,3,2,1,0],  
	          [6,4,2,0],
	          [4,0]]]
	counts = [8,4,2]
	sizes = [1,2,4]
	
	def __init__(self, data, bits_size, cast=False, shape=None):
		self.log = int(math.log2(bits_size))
		if math.log2(bits_size) != self.log:
			msg = "SimpleBitsArray bits_size must be power of 2"
			raise Exception(msg)
		self.data = self._init_data(data, bits_size, cast, shape)

	def _init_data(self, data, bits_size, cast, shape):
		convert_shape = (cast == False) or shape is not None
		if isinstance(data, list):
			data = np.array(data)
		if cast == True:
			data = data.view(np.uint8)
		shape = shape or data.shape
		if convert_shape:
			shape = self._convert_shape(shape, bits_size)
		if cast == True:
			data = data.reshape(shape)
		else:
			#init_data = np.ndarray(shape, dtype=np.uint8)
			#self.data = init_data
			#self.assign(data)
			#data = self.data
			data = self._convert_data(data, shape)
		return data
		
	
	@staticmethod
	def _convert_shape(shape, bits_size):
		shape = tuple(list(shape[:-1]) + [(bits_size * shape[-1]) // 8])
		return shape
		
	@staticmethod
	def zeros(shape, bits_size):
		shape = self._convert_shape(shape, bits_size)
		data = np.zeros(shape, dtype=np.uint8)
		return SimpleBitsArray(data, bits_size)

	@property
	def size(self):
		return self.data.size * self.counts[self.log]
		
	@property
	def shape(self):
		count = self.counts[self.log]
		shape = [s for s in self.data.shape]
		shape[-1] *= count
		return shape
		
	def get_value(self, row, idx):
		# retrieves the value at idx within row (i.e. leaf array)
		#
		# where idx is the index of a value packed into an item 
		# within a row of items
		#
		# [ v1v2v3v4 v5v6v7v8 v9v10v11v12 v13v14v15v16 ]
		#   <------> <------> <---------> <---------->
		#    1 item
		# 
		# where there are count values per item of the underlying array 
		# datatype (i.e. byte)
		count = self.counts[self.log]
		row_idx = idx // count
		mask_idx = idx % count
		mask = self.masks[self.log][mask_idx]
		shamt = self.shamts[self.log][mask_idx]
		return (row[row_idx] & mask) >> shamt
		
	def set_value(self, row, idx, value):
		count = self.counts[self.log]
		row_idx = idx // count
		mask_idx = idx % count
		mask = self.masks[self.log][mask_idx]
		shamt = self.shamts[self.log][mask_idx]
		row[row_idx] = (row[row_idx] & ~mask) | \
				       ((value << shamt) & mask)
		
	@property
	def values(self):
		"""
		Unpacks the bitfield values into a bytes array.
		"""
		count = self.counts[self.log]
		data = self.data.ravel()
		res = [self.get_value(data, idx) for idx in range(len(data)*count)]
		res = np.array(res, dtype=np.uint8).reshape(self.shape)
		return res
	
	def _convert_data(self, data, shape):
		"""
		Packs a bytes array with the initial bitfield values into a
		data array.
		
		Quicker than assign. 
		TODO: make assign work like this so that it can be used instead
		
		:return: the data array 
		"""
		if isinstance(data, SimpleBitsArray):
			data = data.values
		if not isinstance(data, np.ndarray):
			data = np.array(data)
		size = data.size
		count = self.counts[self.log]
		masks = self.masks[self.log]
		shamts = self.shamts[self.log]
		datas = data.ravel().reshape((size // count, count))
		datas = ((datas << shamts) & masks).T
		data = np.bitwise_or.reduce(datas).reshape(shape)
		return data
		
	def _convert_slice(self, slc):
		"""
		Converts a 1-d bitfield array slice to a 1-d byte array slice.
		
		Simply scales the range by number of fields per byte.
		"""
		count = self.counts[self.log]
		if slc.start % count != 0 or slc.stop % count != 0 \
		 or (slc.step is not None and slc.step % count != 0):
			raise Exception("slice indices must be multiples of \
				number of items per byte")
		start = slc.start // count
		stop = slc.stop // count
		step = (slc.step or count) // count
		return slice(start, stop, step)
	
	def assign(self, other):
		"""
		Assigns a value to the entire bitfield array. 
		
		To fill the array, the value is tiled if singular or of length 
		which is a divisor of row/leaf array length.
		
		This will typically be used to set the values of a slice/view of
		an array rather than the full array itself.
		""" 
		def iterate_leaf_arrays(array):
			def indices(shape, append=[]):
				if len(shape) != 1:
					for idx in range(shape[0]):
						yield from indices(shape[1:], append+[idx])
				else:
					for idx in range(shape[0]):
						yield tuple(append+[idx])
			if len(array.shape) == 1:
				yield array
				return
			for idx in indices(array.shape[:-1]):
				yield array[idx]
		
		if isinstance(other, SimpleBitsArray):
			other = other.values
		elif isinstance(other, int):
			other = [other]
		# data = self.data.reshape(-1)
		# data = self.data
		other = np.array(other).ravel()
		count = self.counts[self.log]
		reps = math.ceil(self.data.size*count / other.size)
		other = np.tile(other, reps)
		values = (value for value in other)
		leaf_size = self.data.shape[-1]
		for data in iterate_leaf_arrays(self.data):
			for idx in range(count*leaf_size):
				value = next(values)
				self.set_value(data, idx, value)

	def view(self, dtype):
		return self.data.view(dtype)
		
	def __getitem__(self, key):
		"""
		Retrieves the value(s) of one or more fields in the array. 
		
		Can either be
		- the value of a single field in an n-d bitfield array
		- a subarray of an n-d bitfield array
		- a slice of an n-d bitfield array
		
		Subarrays and slices themselves are returned as SimpleBitsArrays,
		and are views of the source array (i.e. setting modifies the 
		corresponding subset of the source array and is equivalent to 
		calling assign() on the subarray or slice).
		
		(functionality is mostly the same as that of numpy array)
		"""
		slen = len(self.data.shape)
		if slen == 1:
			if isinstance(key, int):
				return self.get_value(self.data, key)
			if isinstance(key, slice):
				key = self._convert_slice(key)
			if isinstance(key, tuple):
				msg = "cannot use tuple index" + \
				      "for single-dimensional array"
				raise Exception(msg)
		elif isinstance(key, tuple) and slen == len(key):
			if all(isinstance(k, int) for k in key):
				row = self.data[key[:-1]]
				return self.get_value(row, key[-1])
			elif isinstance(key[-1], int):
				raise Exception("not supported")
			else:
				key = list(key)
				key[-1] = self._convert_slice(key[-1])
				key = tuple(key)
		return SimpleBitsArray(self.data[key], 2**self.log, cast=True)
		
	def __setitem__(self, key, value):
		"""
		Sets the value(s) of one or more fields in the array.
		
		Calls assign() on the subarray or slice of the array, and
		otherwise set_value on the 1-d leaf row of the array with idx
		for singular values.
		"""
		# retrieve subarray with get and assign value with assign
		slen = len(self.data.shape)
		if isinstance(key, tuple):
			if len(key) == 1: key = key[0]
		if isinstance(key, int) and slen == 1:
			self.set_value(self.data, key, value)
			return
		sub = self[key]
		if not isinstance(sub, SimpleBitsArray):
			sub = self[key[:-1]]  # should give slen == 1
			sub[key[-1]] = value  # 
			#self.set_value(self[key[:-1]].data, key[-1], value)
		else:
			print(value)
			sub.assign(value)

	def __repr__(self):
		"""
		Returns the string representation of the bitfield array.
		
		Basically just the string representation of the numpy array of
		unpacked field values.
		"""
		count = self.counts[self.log]
		data = self.data.ravel()
		values = [self.get_value(data, idx) 
				  for idx in range(len(data)*count)]
		res = str(np.array(values).reshape(self.shape))
		return f"SimpleBitsArray(\n{res})" 

def main():
	test = np.array(np.split(np.array(range(16), dtype=np.uint8), 4))
	test2 = SimpleBitsArray(test, 4)
	print(test2[0:2,0:2])
	return test, test2

if __name__ == '__main__':
	main()
	
	

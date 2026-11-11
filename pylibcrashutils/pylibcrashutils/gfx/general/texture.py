import math
import numpy as np

from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.general.geom_comp import *

from pylibcrashutils.gfx.general.array import array_split_count

from pylibcrashutils.general.bitsarray import SimpleBitsArray

def get_factors(count):
	factors = {}
	for i in range(1,count+1):
		for j in range(1,count+1):
			idx = i*j
			if idx not in factors:
				factors[idx] = []
			factors[idx].append((i,j))
	return factors
factors = get_factors(256)
factors = dict([(k,sorted(v,key=lambda d:abs(d[0]-d[1])))
             for k,v in factors.items()])

def split_range(rng, count):
	res = []
	len = (rng[1] - rng[0]) // count
	start = rng[0] 
	for idx in range(count-1):
		res.append((start, start+len))
		start = start+len
	end = start+len+((rng[1]-rng[0])%count)
	res.append((start, end))
	return res

def groupby(iterable, *keys):
	groups = {}
	key = keys[0]
	if isinstance(key, str):
		key = lambda item: item[key]
	for item in iterable:
		group_key = key(item)
		if group_key not in groups:
			groups[group_key] = []
		groups[group_key].append(item)
	if len(keys) > 1:
		for group_key in groups:
			groups[group_key] = groupby(groups[group_key], *keys[1:])
	return groups

class RangeAlloc:
	def __init__(self, size):
		self.size = size
		self.free = [(0,size)]
		self.used = []
	
	def alloc(self, size):
		for idx, free in enumerate(self.free):
			if size < (free[1] - free[0]):
				ranges = [(free[0],free[0]+size),(free[0]+size,free[1])]
				self.used.append(ranges[0])
				self.free.pop(idx)
				self.free = ranges[1:] + self.free
				return ranges[0]
		return None
		
	def alloc_multi(self, size, count):
		size = size * count
		res = self.alloc(size)
		if res is None:
			return None
		idx = self.used.index(res)
		self.used.pop(idx)
		rngs = split_range(res, count)
		self.used += rngs
		return rngs
		
class Rect2dAlloc:
	"""
	2-dimensional region allocator
	
	works on the same premise as 1d range allocator, but in 2d;
	
	alloc in 1d allocates a single range; alloc_multi in 1d allocates n
	contiguous ranges of equal size (akin to 'array' allocation in c)
	alloc in 2d allocates a single region; alloc_multi in 2d allocates
	n contiguous regions of equal dimensions; since this is 2d it is 
	also possible to specify the shape of the contiguous regions 
	(ex. 3x2 vs 2x3)
	"""
	def __init__(self, dim):
		"""
		Constructs an allocator with initial free region of the 
		specified dimensions.
		""" 
		self.dim = dim
		self.free = [Rect2d(Point(0,0),dim)]
		self.used = []
		
	def alloc(self, dim):
		"""
		Allocates a region (rect2d) of the specified dimensions.
		"""
		for idx, free in enumerate(self.free):
			free = self.free[idx]
			if dim.w <= free.dim.w and dim.h <= free.dim.h:
				rects = slice_rect2d(free, [free.loc + dim], False)
				self.used.append(rects[0])
				self.free.pop(idx)
				self.free = rects[1:] + self.free
				return rects[0]
		return None
		
	def alloc_multi(self, dim, count):
		"""
		Allocates a number of contiguous regions with specified 
		dimensions, where count is the shape of the contiguous regions
		"""
		size = Dimensions(dim.w*count.w, dim.h*count.h)
		res = self.alloc(size)
		if res is None:
			return None
		idx = self.used.index(res)
		self.used.pop(idx)
		rects = split_rect2d(res, [count.w-1, count.h-1])
		self.used += rects
		return rects
		
	def slice(self, loc):
		"""
		Slices the allocator into multiple sub-allocators at the given
		location.
		"""
		bound = Rect2d(Point(0,0), self.dim)
		frees = slice_rects2d(self.free, [loc], bound)
		useds = slice_rects2d(self.used, [loc], bound)
		bounds = slice_rect2d(bound, [loc])
		allocs = []
		for free, used, bound in zip(frees, useds, bounds):
			alloc = Rect2dAlloc(bound.dim)
			alloc.free = free
			alloc.used = used
			allocs.append(alloc)
		return allocs

class PixelFormat:
	"""
	Describes the format of a texture. 
	
	Holds context information for the conversion of texture data between 
	different formats. Includes a string describing the format of pixels 
	in the context and a palette if the format is indexed/paletted. 
	
	Each texture has a pixel format and multiple textures can have the
	same format. Pixel format is considered internal to the texture 
	because it is what is used to convert to other formats.
	"""
	palette_count = 0 # id counter; for now
	def __init__(self, fmt, palette=None):
		self._fmt = fmt
		self._color_fmt = self.fmt.split('_')[-1]
		self._palette = self._init_palette(palette)
		self.parse_map = {}
		self.unparse_map = {}
		
	@property
	def fmt(self):
		return self._fmt
		
	@property
	def palette(self):
		return self._palette
	
	@property
	def color_fmt(self):
		#if '_palette' not in self.__dict__ or self.palette is None:
		#	return self.fmt.split('_')[-1]
		#return self.palette.format.fmt
		return self._color_fmt
		
	@property
	def index_fmt(self):
		#if '_palette' not in self.__dict__ or self.palette is None:
		#	return None
		parts = self.fmt.split('_')
		if len(parts) < 2:
			return None
		return parts[0]
		
	@property
	def dtype(self):
		# smallest datatype which can hold pixel values (either index or color)
		if self.index_fmt in ['I4', 'I8']:
			return np.uint8
		else:
			return self.color_dtype
			
	@property
	def color_dtype(self):
		if self.color_fmt in ['RGBA5551', 'ABGR1555']:
			return np.uint16
		elif self.color_fmt in ['RGBA8888', 'ABGR8888']:
			return np.uint32
		else:
			raise Exception("unsupported pixel format")
		
	@property
	def bitlen(self):
		# bitlength of pixel values (either index or color)
		if self.index_fmt == 'I4':
			return 4
		elif self.index_fmt == 'I8':
			return 8
		elif self.color_fmt in ['RGBA5551', 'ABGR1555']:
			return 16
		elif self.color_fmt in ['RGBA8888', 'ABGR8888']:
			return 32
		else:
			raise Exception("unsupported pixel format")
		
	@property
	def palette_size(self):
		if self.index_fmt == 'I4':
			return 16
		elif self.index_fmt == 'I8':
			return 256
		else:
			return None

	def _init_palette(self, palette):
		"""
		Creates a (1d) Texture object for this format's initial palette.
		[*if appropriate conditions are met]
		
		- if the format is paletted and no list of initial colors is 
		  passed, then a zero-initialized Texture of the format palette 
		  size is returned
		- if a list of initial colors is passed but the format 
		  is not paletted then it is readjusted to an appropriate format
		- the list of initial colors is then converted to a 1d Texture
		  of the format palette size (if not already passed as a Texture)
		  and then returned
		- otherwise the format is not paletted and no initial list is 
		  passed, so no palette is returned
		  
		:param palette: array or texture with initial colors
		:return: a 1d Texture
		"""
		def _fmt_from_palette(palette):
			if not isinstance(palette, Texture):
				palette_size = len(palette)
			else:
				palette_size = len(palette.data)
			return f'I{palette_size}_{self._fmt}' 
		data = None
		if palette is None and self.index_fmt is not None:
			# if no palette passed to arguments but format is paletted
			# then allocate data for the palette
			data = np.zeros(self.palette_size, self.color_dtype)
		elif palette is not None:
			# if a palette is passed to arguments but format not paletted
			# then readjust the format to indicate it is paletted
			if self.index_fmt is None:
				self._fmt = _fmt_from_palette(palette) 
			# also grab the palette data if not passed as a texture
			if not isinstance(palette, Texture):
				data = palette
		if data is not None:
			# if palette wasnt already passed as a Texture then convert it
			dim = Dimensions(self.palette_size, 1)
			key = f'pal_{PixelFormat.palette_count}'
			palette = Texture(key, dim, data, self.color_fmt)
			PixelFormat.palette_count += 1
		else:
			palette = None
		return palette
	
	def copy(self):
		"""
		Returns a copy of this format.
		
		:return: the copied object
		"""
		return PixelFormat(self.fmt, self.palette)

	def parse(self, pixel):
		"""
		Parses a pixel value of this format into a tuple with RGBA 
		components.
		
		If the format is paletted then the pixel value should be a
		palette color index and the result will be the parsed palette 
		color.
		
		:param pixel: pixel value or palette color index
		:return: tuple of RGBA components
		"""
		if pixel in self.parse_map:
			return self.parse_map[pixel]
		if self.palette is not None:
			pixel = self.palette.data[0][pixel]
		if self.color_fmt == 'RGBA8888':
			r = (pixel & 0xFF000000) >> 24
			g = (pixel & 0xFF0000) >> 16
			b = (pixel & 0xFF00) >> 8
			a = (pixel & 0xFF) >> 0
		elif self.color_fmt == 'ABGR8888':
			r = (pixel & 0xFF) >> 0
			g = (pixel & 0xFF00) >> 8
			b = (pixel & 0xFF0000) >> 16
			a = (pixel & 0xFF000000) >> 24
		elif self.color_fmt == 'RGBA5551':
			r = ((pixel & 0xF800) >> 11) * 17
			g = ((pixel & 0x7C0) >> 6) * 17
			b = ((pixel & 0x3E) >> 1) * 17
			a = (pixel & 1) * 255
		elif self.color_fmt == 'ABGR1555':
			r = ((pixel & 0x1F) >> 0) * 17
			g = ((pixel & 0x3E0) >> 5) * 17
			b = ((pixel & 0x7C00) >> 10) * 17
			a = ((pixel & 0x8000) >> 15) * 255
		else:
			r,g,b,a = 0,0,0,0
		self.parse_map[pixel] = (r,g,b,a)
		return (r,g,b,a)
	
	def unparse(self, components):
		"""
		Converts a tuple of RGBA components to a pixel value of this 
		format.
		
		If the format is paletted then the result value will be the 
		index of the 'nearest' palette color rather than a direct 
		encoded color.
		
		:param components: tuple of RGBA components
		:return: pixel value or palette color index
		"""
		components = tuple(components)
		if components in self.unparse_map:
			return self.unparse_map[components]
		if self.palette is not None:
			if 'color_cache' not in self.__dict__:
				format = self.palette.format
				data = self.palette.data[0]
				colors = [format.parse(color) for color in data]
				self.__dict__['color_cache'] = np.array(colors)
			colors = self.color_cache
			c1 = colors
			c2 = np.array([components]).repeat(self.palette_size, axis=0)
			idx = np.argmin(np.sum((c2 - c1) ** 2, axis=1))
			self.unparse_map[components] = idx
			return idx
		if self.color_fmt == 'RGBA8888':
			r = (components[0] << 24)
			g = (components[1] << 16)
			b = (components[2] << 8)
			a = (components[3])
		elif self.color_fmt == 'ABGR8888':
			r = (components[0])
			g = (components[1] << 8)
			b = (components[2] << 16)
			a = (components[3] << 24)
		elif self.color_fmt == 'RGBA5551':
			r = (components[0] // 17) << 11
			g = (components[1] // 17) << 6
			b = (components[2] // 17) << 1
			a = (components[3] // 128)
		elif self.color_fmt == 'ABGR1555':
			r = (components[0] // 17)
			g = (components[1] // 17) << 5
			b = (components[2] // 17) << 10
			#a = (components[3] // 128) << 15
			a = 128
		else:
			r,g,b,a = 0,0,0,0
		pixel = r | g | b | a
		self.unparse_map[components] = pixel
		return pixel
			
	def convert(self, data, fmt):
		"""
		Converts an array of pixel data of this format to a new format.
		
		The converted pixel array is returned along with the new format
		object. Note that the format object will include a new
		palette if the destination format is paletted.
		
		:param data: array of pixels
		:param fmt: destination format or format id
		:return: the converted array and new PixelFormat
		"""
		if isinstance(data, SimpleBitsArray):
			data = data.values
		data = data.view(dtype=self.dtype)
		shape = data.shape
		if len(shape) > 1:
			product = 1
			tmp = [product := product*val for val in shape]
			data = data.reshape((product,))
		pixels = [self.parse(pixel) for pixel in data]
		if not isinstance(fmt, PixelFormat):
			fmt = PixelFormat(fmt)
			if fmt.palette is not None:
				fmt.build_palette(pixels)
		new_data = np.array([fmt.unparse(pixel) for pixel in pixels],
							 dtype=fmt.dtype).reshape(shape)
		if fmt.bitlen < 8:
			new_data = SimpleBitsArray(new_data, fmt.bitlen)
		new_fmt = fmt
		if fmt.bitlen >= 8:
			print("new_data.dtype:", new_data.dtype)
		else:
			print(f"new_data.type: SimpleBitsArray({fmt.bitlen})")
		print("new_data.shape:", new_data.shape)
		print("new_fmt.fmt:", new_fmt.fmt)
		return new_data, new_fmt
		
	def cast(self, data, fmt):
		"""
		Casts an array of pixel data of this format to another format.
		
		Note that no conversion of the data is done. 
		
		Fmt can be an existing format or an identifier string. If it is
		an identifier for a paletted format then the cast will fail as
		palette must exist separately from the data.
		
		:param data: array of pixels
		:param fmt: destination format or format id
		:return: the casted array and new PixelFormat
		"""
		if not isinstance(fmt, PixelFormat):
			fmt = PixelFormat(fmt)
			if fmt.palette is not None:
				raise Exception("cast failed")
		if isinstance(data, SimpleBitsArray):
			data = data.data
		data = data.view(dtype=fmt.dtype)
		if fmt.bitlen < 8:
			data = SimpleBitsArray(data, fmt.bitlen, cast=True)
		return data, fmt
		
	def build_palette(self, pixels):
		"""
		Builds a palette for this format from an array of parsed pixel 
		data.
		
		:param pixels: array of parsed pixels
		"""
		if self.palette is None:
			raise Exception("cannot build palette for unpaletted format")
		color_fmt = self.palette.format
		colors, counts = np.unique(pixels, axis=0, return_counts=True)
		colors_sorted = colors[np.argsort(-counts)][:self.palette_size]
		palette_data = np.array([color_fmt.unparse(color) 
			for color in colors_sorted], dtype=color_fmt.dtype)
		palette_data = np.resize(palette_data, self.palette_size)
		palette_data = palette_data.reshape(1,self.palette_size)
		self.palette.data = palette_data
	
	def diff(self, fmt):
		"""
		Returns the size ratio between [pixel bitlengths of] this format
		and another.
		
		Useful for computing shape of casted data.
		
		:param fmt: other format or format id
		:return: size ratio
		"""
		if not isinstance(fmt, PixelFormat):
			fmt = PixelFormat(fmt)
		diff = self.bitlen / fmt.bitlen
		return diff
	
	def convert_dim(self, dim, fmt):
		"""
		Converts dimensions of an array of pixel data of this format to 
		dimensions after casting to another format.
		
		:param dim: dimensions
		:return: converted dimensions
		"""
		diff = self.diff(fmt)
		dim = Dimensions(dim.w * diff, dim.h)
		return dim
			
	def convert_area(self, area, fmt):
		"""
		Converts area of an array of pixel data of this format to area
		after casting to another format.
		
		:param area: area
		:return: converted area
		"""
		diff = self.diff(fmt)
		area *= diff
		return area
	
		
class Texture:
	"""
	A 2 dimensional array of pixels with a format and identifier key.
	"""
	def __init__(self, key, dim, data=None, fmt='ABGR8888'):
		# format is ABGR8888 by default rather than RGBA8888 because we
		# expect an array of raw RGBA8888 bytes to be casted to array of 
		# uint32, which byteswaps as ABGR8888 due to endianness
		self.key = key
		self._format = self._init_format(fmt)
		self.data = self._init_data(self.format, dim, data)	
		
	@staticmethod
	def _init_format(fmt):
		if isinstance(fmt, PixelFormat):
			return fmt
		return PixelFormat(fmt)
		
	@staticmethod
	def _init_data(format, dim, data=None):
		"""
		Returns the underlying array of pixel data for an instance
		given the input format, dimensions, and optional initial values.
		
		Note that if the initial values array is not in the specified 
		format then it will be casted.
		
		:param format: PixelFormat for the instance
		:param dim: dimensions of the array
		:param data: optional array of initial [pixel] values
		:returns: casted and reshaped pixel array
		"""
		shape = (int(dim.h), int(dim.w))
		if isinstance(data, list):
			data = np.array(data, dtype=format.dtype)
		if format.bitlen == 4 and data is None:
			data = SimpleBitsArray.zeros(shape, 4)
		elif format.bitlen == 4:
			if isinstance(data, SimpleBitsArray):
				return data #????????
			data = SimpleBitsArray(data, 4, shape=shape)
		elif data is None:
			data = np.zeros(shape, dtype=format.dtype)
		else:
			data = data.view(dtype=format.dtype).reshape(shape)
		return data
		
	def copy(self, dst, dst_loc=None):
		"""
		Copies the pixels of this texture into a subregion of another 
		texture. 
		
		:param dst: destination texture
		:param dst_loc: optional destination location; defaults to (0,0)
		"""
		dst_loc = dst_loc or Point(0,0)
		for y in range(int(self.dim.h)):
			for x in range(int(self.dim.w)):
				dst.data[int(dst_loc.y)+y][int(dst_loc.x)+x] = \
					self.data[int(self.dim.h)-y-1][x]	
	
	@property
	def format(self):
		return self._format
		
	@property
	def dim(self):
		return Dimensions(self.data.shape[1], self.data.shape[0])
	
	@property
	def area(self):
		return self.data.size

	@property
	def bytes(self):
		return self.data.reshape((self.area,)).view(np.uint8)
			
	def convert(self, fmt, inplace=False):
		"""
		Converts the texture to a new format.
		
		:param fmt: destination format or format id
		:param inplace: optional flag to enable inplace conversion
		:return: the converted texture
		"""
		print(f"converting {self.key} from {self.format.fmt} to {fmt}")
		data, format = self.format.convert(self.data, fmt)
		if inplace == True:
			self.data = data
			self._format = format
			return self
		texture = Texture(self.key, self.dim, data, format)
		return texture
		
	def cast(self, fmt, inplace=False):
		"""
		Casts the texture to another format.
		
		:param fmt: destination format or format id
		:param inplace: optional flag to enable inplace cast
		:return: the casted texture
		"""
		data, format = self.format.cast(self.data, fmt)
		if inplace == True:
			self.data = data
			self._format = format
			return self
		dim = Dimensions(data.shape[1], data.shape[0])
		texture = Texture(self.key, dim, data, format)
		return texture

	def area_as(self, fmt):
		"""
		Returns the area of the texture when casted to another format.
		
		:param fmt: other format or format id
		:return: texture area
		"""
		return self.format.convert_area(self.area, fmt)	
	
class Subtexture(Texture):
	"""
	A texture which occupies a region of a larger parent texture.
	
	Since Subtexture is a Texture, it should implement dim and data;
	dim is the dimensions of the region (rect), and data is a 2d view 
	of the region of pixel data in the parent texture; 
	in addition there is loc, a shorthand for the location of the region 
	(rect), and uvs, the [0-1] normalized coordinates of the subtexture
	region vertices
	"""
	def __init__(self, parent, key, rect, data=None, fmt=None):
		"""
		Constructs a subtexture of a parent texture.
		
		If an array of initial pixel data is specified (as 'data'), it 
		will be copied into the rect region of the parent texture. 
		Otherwise the existing pixel data within the region is used.
		
		If a fmt is specified which differs from that of the parent 
		texture, the parent reference is casted to view the pixel data 
		in the correct format.
		
		:param parent: parent texture
		:param key: identifier
		:param rect: region of parent texture 
		:param data: optional array of initial pixel data
		:param fmt: optional format (otherwise inherited from parent)
		"""
		self.key = key
		self.rect = rect
		self.parent = parent if fmt is None else parent.cast(fmt)
		if data is not None:
			self.data[:] = data
		
	@staticmethod
	def from_texture(texture, loc, parent):
		"""
		Constructs a subtexture from an existing texture. The data of 
		the existing texture is copied into the parent texture at the
		specified location.
		
		:param texture: existing texture
		:param loc: location within parent
		:param parent: parent texture
		:return: the new subtexture
		"""
		rect = Rect2d(loc, texture.dim)
		key = texture.key
		data = texture.data
		format = texture.format
		subtexture = Subtexture(parent, key, rect, data, format)
		return subtexture
	
	@property
	def format(self):
		return self.parent.format
				
	@property
	def dim(self):
		return self.rect.dim
	@dim.setter
	def dim(self, value):
		self.rect.dim = value
		
	@property
	def loc(self):
		return self.rect.loc
	@loc.setter
	def loc(self, value):
		self.rect.loc = value
		
	@property
	def data(self):
		data = self.parent.data
		return self.parent.data[int(self.rect.p1.y):int(self.rect.p2.y),
								int(self.rect.p1.x):int(self.rect.p2.x)]
				
	@property
	def uvs(self):
		loc = self.loc / self.parent.dim
		dim = self.dim / self.parent.dim
		rect = Rect2d(loc, dim)
		uvs = rect.to_quad().verts
		return uvs
		
	def cast(self, fmt, inplace=False):
		"""
		Casts the subtexture to a new format.
		
		Casting a subtexture casts its view of the parent texture and 
		adjusts its location and dimensions accordingly.
		
		:param fmt: destination format or format id
		:param inplace: optional flag to enable inplace conversion
		:return: the casted subtexture
		"""
		key, rect = self.key, self.rect.copy()
		parent = self.parent.cast(fmt)
		scale = parent.dim.w / self.parent.dim.w
		rect.loc.x *= scale
		rect.dim.w *= scale
		if inplace == False:
			subtexture = Subtexture(parent, key, rect)
			return subtexture
		self.parent = parent
		self.rect = rect

	def convert(self, fmt):
		"""
		Converts the subtexture to a texture with new format.
		
		Note that conversion to a -subtexture- of new format is not 
		allowed. If this behavior is desired, convert the parent atlas.
		(TODO: implement TextureAtlas.convert, .cast)
		
		:param fmt: destination format or format id
		:return: the converted texture
		"""
		print(f"converting {self.key} from {self.format.fmt} to {fmt}")
		data, format = self.format.convert(self.data, fmt)
		dim = Dimensions(data.shape[1], data.shape[0])
		texture = Texture(self.key, dim, data, format)
		return texture
		
class TextureGroup:
	"""
	A group of textures.
	
	Textures can be added to and retrieved from a group by key. 
	Retrieval works recursively for any textures which are TextureAtlases.
	
	There are functions for:
	  - constructing a dictionary of texture dimensions to list of textures
	  - distributing group textures amongst multiple groups
	  - packing group textures into a TextureAtlas
	  - distributing group textures into separate TextureAtlases
	    (as a group)
	"""
	def __init__(self, textures=None):
		self.textures = {} if textures is None \
						else {tex.key: tex for tex in textures}

	def add(self, texture):
		"""
		Adds a texture to the group.
		
		:param texture: texture to add
		"""
		self.textures[texture.key] = texture
		
	def get(self, key):
		"""
		Retrieves the texture with the given key from the group.
		
		For any texture which is an atlas the subtextures are also 
		searched.
		
		:param key: texture key
		:return: group texture
		"""
		atlases = [texture for texture in self.textures.values()
				   if isinstance(texture, TextureAtlas)]
		for atlas in atlases:
			subtexture = atlas.get(key)
			if subtexture is not None:
				return subtexture
		return self.textures.get(key)
	
	def get_map(self, *keys):
		"""
		Returns a dictionary of all textures in the group, keyed on 
		a certain attribute(s).
	
		Acceptable values for keys are 'dimension', 'palette', 'fmt', 
		and 'format'. The dictionary may be nested as multiple keys are
		allowed.
		
		:param keys: list of attributes to key on
		:return: dictionary of group textures 
		"""
		textures = self.textures.values()
		key_map = {
			'dimension': lambda tex: tex.dim,
			'palette': lambda tex: tex.format.palette,
			'fmt': lambda tex: tex.format.fmt,
			'format': lambda tex: tex.format
		}
		keys = [key_map[key] for key in keys]
		textures = sorted(textures, key=lambda tex:-tex.dim.w*tex.dim.h)
		textures = groupby(textures, *keys)
		textures = {k:v for k,v in textures.items() if k is not None}
		return textures
		# textures = dict(sorted(textures.items(), 
		#				key=lambda kv:-kv[0].w*kv[0].h))
	
	def get_dimension_map(self):
		"""
		Returns a dictionary of all textures in the group
		keyed by dimension.
		
		:return: texture dictionary
		"""
		return self.get_map('dimension')
		
	def get_palette_map(self):
		"""
		Returns a dictionary of all textures in the group
		keyed by palette.
		
		:return: texture dictionary
		"""		
		return self.get_map('palette')
		
	def get_format_map(self):
		"""
		Returns a dictionary of all textures in the group
		keyed by format (string).
		
		:return: texture dictionary
		"""
		return self.get_map('fmt')
		
	def get_max_format(self):
		"""
		Returns the format which has the longest bitlength amongst the 
		group textures' formats.
		"""
		formats = list(self.get_map('format'))
		format = max(formats, key=lambda fmt: fmt.bitlen)
		return format
		
	def area_as(self, fmt=None):
		"""
		Computes the total area of the group textures after casting to 
		a dest format.
		"""
		if fmt is None:
			fmt = self.get_max_format().fmt
		area = sum([tex.area_as(fmt) for tex in self.textures.values()])
		return area
		
	def distribute(self, dim, fmt=None, include_palettes=False):
		"""
		Evenly distributes the group textures amongst n separate groups
		such that the total area of textures in each group (as casted to 
		fmt) does not exceed the area of dim.
		
		The function assumes that the result groups will be packed into
		atlases of the input dim and fmt. To pack a group's textures it 
		is necessary to first cast each texture to the atlas format (fmt). 
		This will change the areas of any textures of formats which 
		differ in bitlength. The logic for this function takes this into 
		consideration.
		
		:param dim: dimensions with max group area
		:param fmt: optional max format or format id of the groups
		:return: the result TextureGroups
		"""
		area = self.area_as(fmt)
		if include_palettes == True:
			palettes = list(self.get_palette_map())
			area += sum(palette.area_as(fmt) for palette in palettes)
		new_count = math.ceil(area / (dim.w*dim.h))
		fdim_map = groupby(self.textures.values(), 
						   lambda tex: (tex.format.fmt, tex.dim))
		textures = {k: array_split_count(v, new_count) 
					for k,v in fdim_map.items()}
		groups = [TextureGroup([texture 
				  for val in textures.values() for texture in val[idx]]) 
				  for idx in range(new_count)]
		return groups
		
	def distribute_using_palettes(self, dim, fmt=None, threshold=0.9):
		"""
		Distributes the group textures such that the total area of 
		textures and palettes in each group (as casted to fmt) does not 
		exceed the area of dim, and textures which use the same palette 
		are placed into the same groups.
		
		Note that there may be more textures of given dimensions in one
		group than another because this distributes so that an equal
		number of palettes are placed into each group.
		
		:param dim: dimensions with max group area
		:param fmt: optional max format or format id of the groups
		:param threshold: similarity threshold for palette reduction
		:return: the result TextureGroups
		"""
		def circular(list):
			while True:
				for item in list:
					yield item
		def zip_gen(gens):
			while True:
				vals = [next(gen, None) for gen in gens]
				vals = [val for val in vals if val is not None]
				if len(vals) == 0: break
				yield vals
				
		# first reduce the number of palettes if possible
		self.reduce_palettes(threshold)
		
		# compute the total area as: 
		# the sum of areas of all group textures and palettes (as casted 
		# to the dst format)
		palettes = list(self.get_palette_map())
		total_area = self.area_as(fmt) + \
					 sum(palette.area_as(fmt) for palette in palettes)
		
		# compute the number of result groups as the total area over the
		# area of dim (i.e. the area of the atlases the groups pack to)
		max_area = dim.w*dim.h
		new_count = math.ceil(total_area / max_area)
		
		# create a list of the new groups and their [initial] 
		# corresponding cumulative palette areas
		# then create a circular iterator which will be used to do the
		# even distribution/population
		groups = [[TextureGroup(), [0]] for idx in range(new_count)]
		groups_gen = circular(groups)
		
		# get nested map of group textures by dimension and then palette
		# then create a list of iterators for each dimension, each of 
		# which will iterate the nested palette/textures pairs
		# finally, iterate them in parallel with a zip_gen.
		# for each iteration this will yield a list of items, one item
		# for each dimension, where an item is a tuple with the next set
		# of textures for that dimension of a distinct palette, and the
		# palette itself
		dim_pal_map = self.get_map('dimension', 'palette')
		gens = [iter(pal_map.items()) for pal_map in dim_pal_map.values()]
		for palette_map in zip_gen(gens):
			# cycle to the next group and distribute the next sets of 
			# textures there (and their corresponding palettes) if the 
			# total group area would not exceed the max
			group, palette_area = next(groups_gen)
			for palette, textures in palette_map:
				texture_area = sum([texture.area_as(fmt) for texture in textures])
				tex_palette_area = 0
				if palette is not None:
					tex_palette_area = palette.area_as(fmt)
				prev_group = group
				# for any given iteration, the textures of a particular 
				# dimension may fit the group (bypassing the below loop)
				# and textures of the next size up could overflow 
				# (causing entry to the loop). in case of overflow the
				# following groups in the cycle are tested until there 
				# is a fit, or no group will fit all of the textures as
				# a whole.
				while group.area_as(fmt) + palette_area[0] + \
					  texture_area + tex_palette_area > max_area:
					group, palette_area = next(groups_gen)
					# if no group will fit the textures as a whole (a
					# cycle is made) then distribute them individually
					if group == prev_group:
						while len(textures) > 0:
							while group.area_as(fmt) + palette_area[0] + \
								  textures[0].area_as(fmt) + tex_palette_area > max_area:
								group, palette_area = next(groups_gen)
							texture = textures.pop(0)
							group.add(texture)
						break
				# finally add the textures of this dimension and palette
				# to the group
				for texture in textures:
					group.add(texture)
				# ...and accumulate the palette area for the group; as 
				# it is not as easily computed as texture area 
				palette_area[0] += tex_palette_area
		groups = [group[0] for group in groups]
		return groups
		
	def convert(self, fmt, inplace=False):
		"""
		Converts all of the group textures to a new format.
		
		:param fmt: destination format or format id
		:param inplace: optional flag to enable inplace conversion
		:return: group with the converted textures
		"""
		textures = [texture for texture in self.textures.values()]
		textures = [texture.convert(fmt, inplace) for texture in textures]
		if inplace == True:
			return None
		group = TextureGroup(textures)
		return group
		
	def cast(self, fmt, inplace=False):
		"""
		Casts all of the group textures to a new format.
		
		:param fmt: destination format or format id
		:param inplace: optional flag to enable inplace conversion
		:return: group with the casted textures
		"""
		textures = [texture for texture in self.textures.values()]
		textures = [texture.cast(fmt, inplace) for texture in textures]
		if inplace == True:
			return None
		group = TextureGroup(textures)
		return group
		
	def pack(self, dim, key=None, fmt=None, mode=1, pack_palettes=False):
		"""
		Packs the group textures into a new texture atlas of specified
		dimensions.
		
		To handle textures of different formats, all group textures are 
		casted to the destination format prior to packing.
		
		:param dim: atlas dimensions
		:param key: atlas key
		:param fmt: atlas format or format id
		:param mode: packing mode/algorithm
		:param pack_palettes: flag which enables packing of palettes
		:return: texture atlas
		"""
		def alloc_subtextures(atlas, allocator, dim, textures, mode):
			"""
			Allocates subtextures of dimensions dim to atlas 
			using allocator and algorithm corresponding to mode.
			
			mode 0: for each texture, allocate the upper left portion of 
			        the next available free region which will fit it, 
			        and leave the remaining left over part of the free
			        region (a rect with a rect in the upper left cut out)
			        as free area (split it into 3 rects)
			mode 1: find the 2 factors of the number of textures which
			        are nearest as possible to a square, such that said
			        arrangement of the textures would fit into some 
			        available free region, and then allocate the 
			        complete block of textures as if it were a singular 
			        texture allocated with mode 0; then split the block 
			        as necessary to get the individual locations (dim 
			        will all be the same)
			
			:param atlas: atlas
			:param allocator: allocator
			:param textures: subtextures
			:param mode: packing mode/algorithm
			"""
			if mode == 0:
				for texture in textures:
					rect = allocator.alloc(dim)
					atlas.add(texture, rect.loc)
			elif mode == 1:
				facts = (fact for count in range(len(textures),0,-1)
						      for fact in factors[count])
				for factor in facts:
					shape = Dimensions(*factor)
					rects = allocator.alloc_multi(dim, shape) or []
					if len(rects) > 0:
						break
				for rect, texture in zip(rects, textures):
					atlas.add(texture, rect.loc)
		
		def alloc_palettes(allocator, dim=None):
			if dim is not None:
				# compute dimensions for a subatlas to hold the palettes
				# (if not using the allocator dimensions)
				h_mult = 4
				palettes_area = TextureGroup(
					list(self.get_palette_map())).area_as(fmt) 
				dim_h = h_mult*math.ceil(palettes_area / (dim.w*h_mult))
				dim = Dimensions(dim.w, dim_h)
			else:
				dim = allocator.dim
			# pack the palettes into subatlas and into main atlas
			palette_atlas = self.pack_palettes(dim, "palette_atlas")
			alloc_subtextures(atlas, allocator, dim, [palette_atlas], 0)
			palette_atlas = atlas.get("palette_atlas")
			# replace palettes with the new subtextures
			palette_map = self.get_palette_map()
			for palette, textures in palette_map.items():
				for texture in textures:
					texture.format._palette = palette_atlas.get(palette.key)
			return palette_atlas
						
		if fmt == None:
			fmt = self.get_max_format().fmt
		atlas = TextureAtlas(dim, key, fmt)
		allocator = Rect2dAlloc(dim)
		
		palettes = list(self.get_palette_map())
		if pack_palettes == True and len(palettes) > 0:
			# for mode 2, allocate a predefined region for the palettes
			# if they are all 16 color palettes
			if mode == 2 and not any([pal.area == 256 for pal in palettes]):
				dim = Dimensions(dim.w - 16, dim.h)
				allocator = Rect2dAlloc(dim)
				pal_allocator = Rect2dAlloc(Dimensions(16, dim.h))
				pal_allocator.free[0].loc.x = dim.w
				alloc_palettes(pal_allocator)
				mode = 0
			else:
				alloc_palettes(allocator, dim)
			
		# first cast all group textures to the atlas format
		# this is necessary because all allocation regions must be 
		# in terms of the same format
		group = self.cast(atlas.format)
		dim_map = group.get_dimension_map()
		for dim, textures in dim_map.items():
			alloc_subtextures(atlas, allocator, dim, textures, mode)
		# then cast back to the original format
		for key, texture in atlas.textures.items():
			if self.get(key) is None: continue
			format = self.get(key).format
			texture.cast(format, inplace=True)
		return atlas
		
	def pack_palettes(self, dim, key=None):
		"""
		Packs the group textures' palettes into a new texture atlas of 
		specified dimensions.
		
		:param dim: atlas dimensions
		:param key: atlas key
		:return: texture atlas
		"""
		palettes = list(self.get_palette_map())
		fmt = palettes[0].format
		palette_group = TextureGroup(palettes)
		atlas = palette_group.pack(dim, key, fmt, 0)
		return atlas
		
	def to_atlas_group(self, dim, key=None, fmt=None, **args):
		"""
		Evenly distributes the group textures amongst n separate groups,
		packs the textures of each group into individual atlases,
		and returns them as a texture group.
		
		:param dim: atlas dimensions
		:param key: atlas key function
		:param fmt: atlas format or format id
		:param pack_mode: packing mode/algorithm
		:param pack_palettes: flag which enables packing of palettes
		:param dist_mode: distribution mode/algorithm
		:param threshold: palette reduction threshold (dist_mode==1)
		:return: texture group of atlases
		"""
		key = key or (lambda i:f"atlas_{i}.png")
		if fmt == None:
			fmt = self.get_max_format().fmt
		pack_mode = args.get('pack_mode') or 1
		pack_palettes = args.get('pack_palettes') or True
		dist_mode = args.get('dist_mode') or 1
		threshold = args.get('threshold') or 0.9
		
		if dist_mode == 0:
			groups = self.distribute(dim, fmt, pack_palettes)
		else:
			groups = self.distribute_using_palettes(dim, fmt, threshold)
		atlases = [group.pack(dim, key(idx), fmt, mode=pack_mode,
							  pack_palettes=pack_palettes) 
				   for idx, group in enumerate(groups)]
		atlas_group = TextureGroup(atlases)
		return atlas_group

	def to_list(self):
		return list(self.textures.values())

	def reduce_palettes(self, threshold=0.9):
		"""
		Attempts to reduce the number of palettes used by paletted 
		textures in the group by re-using 'similar' palettes.
		
		:param threshold: similarity threshold; palette pairs above the
						  threshold will be merged into a single palette
		"""
		def palette_similarity(p1, p2):
			"""
			Similarity measure between 2 palettes is defined as
			the sum of the distances between colors in the first palette
			and the nearest colors in the second palette, normalized to
			the 0-1 range.
			
			:param p1: first palette
			:param p2: second palette
			:return: similarity measure
			"""
			p1 = np.array([p1.format.parse(c) for c in p1.data[0]])
			p2 = np.array([p2.format.parse(c) for c in p2.data[0]])
			shape = (p1.shape[0],p2.shape[0],4)
			a1 = np.tile(p1.ravel(),shape[1]).reshape(shape)
			a2 = p2.repeat(shape[0], axis=0).reshape(shape)
			diffs = np.sqrt(np.apply_over_axes(np.sum, np.square(a2 - a1), [2]))
			nearest = np.apply_over_axes(np.min, diffs, [1])
			similarity = 1 - np.sum(nearest)/(510*len(p2))
			return similarity
			
		# get all paletted textures
		textures = [tex for tex in self.textures.values()
				    if tex.format.palette is not None]
		
		# get mapping of format to textures
		format_map = groupby(textures, lambda tex: tex.format)
		formats = [format for format in format_map]
		convert_map = {}
		converted = set()
		while len(formats) > 0:
			f1 = formats.pop(0)
			similarities = {}
			for f2 in formats:
				p1, p2 = f1.palette, f2.palette
				print(f"computing similarity of {p1.key} and {p2.key}")
				similarity = palette_similarity(p1, p2)
				similarities[f2] = similarity
			similar = [format for format, sim in similarities.items()
					   if sim > threshold]
			for sim in similar:
				convert_map[sim] = f1
				formats.remove(sim)
		for f1, f2 in convert_map.items():
			for tex in format_map[f2]:
				if tex in converted: continue
				tex.convert(f2, inplace=True)
				converted.add(tex)
	
class TextureAtlas(Texture, TextureGroup):
	"""
	TextureAtlas is a texture which consists of subtextures.
	
	It combines the functionality of its Subtextures as a TextureGroup 
	with its functionality as a parent Texture to the Subtextures.
	Subtextures' pixel data are views of the parent texture, so no 
	synchronization is necessary.
	"""	 
	def __init__(self, dim, key=None, fmt="ABGR8888"):
		super(TextureAtlas, self).__init__(key, dim, fmt=fmt)
		subtextures = {}
		self.subtextures = subtextures
		self.textures = subtextures
		
	def add(self, texture, loc=None):
		if isinstance(texture, TextureAtlas):
			texture = TextureSubAtlas.from_atlas(texture, loc, self)
		elif not isinstance(texture, Subtexture):
			texture = Subtexture.from_texture(texture, loc, self)
		texture.parent = self
		self.subtextures[texture.key] = texture
		return texture
		
	def get(self, key):
		return self.subtextures.get(key)

class TextureSubAtlas(Subtexture, TextureAtlas):
	"""
	TextureSubAtlas is a subtexture which consists of subtextures.
	"""
	def __init__(self, parent, key, rect, data=None, fmt=None):
		super(TextureSubAtlas, self).__init__(parent, key, rect, data, fmt)
		subtextures = {}
		self.subtextures = subtextures
		self.textures = subtextures
	
	@staticmethod
	def from_atlas(atlas, loc, parent):
		rect = Rect2d(loc, atlas.dim)
		key = atlas.key
		data = atlas.data
		format = atlas.format
		subatlas = TextureSubAtlas(parent, key, rect, data, format)
		subtextures = subatlas.subtextures
		for key in atlas.subtextures:
			subtexture = atlas.subtextures[key]
			if isinstance(subtexture, TextureSubAtlas):
				subtexture = TextureSubAtlas.from_atlas(subtexture, 
					subtexture.loc, subatlas)
			else:
				subtexture = Subtexture(subatlas, key, subtexture.rect)
			subtextures[key] = subtexture
		return subatlas
		
def texture_region_to_rect(texture, poly, dim):
	"""
	Transforms a polygonal region of a texture and its mirrored region
	(together forming a parallelogram) to a new rectangular texture.
	
	[normalized] uv coordinates specified in poly will wrap and tile if 
	outside of the 0.0-1.0 range.
	
	This function can be used to convert subtexture data for uvs 
	describing non-right triangular/rectangular and/or wrapping regions
	to rectangular non-wrapping subtextures, enabling the uvs to be 
	remapped to right-triangular/rectangular non-wrapping regions. This 
	is necessary when only such uvs (non-wrapping, rectangular) are 
	allowed by the target (i.e. TextureAtlas).
	
	There is an obvious loss of quality involved in many cases due to
	skewing and scaling of the region to fit the new texture; this can
	be reduced by partitioning the source polygon at texture wrapping 
	points.
	
	:param texture: source texture
	:param poly: poly with vertices with the normalized region coords
	:param dim: dimensions of the [transformed] result texture
	:return: result texture
	"""
	v0, v1, v2 = tuple(poly.verts)

	winding = get_poly_winding2(poly)
	
	ul, ur, ll, lr = [poly.verts[winding.index(corner)].vmul(texture.dim)
					  if corner in winding else None
					  for corner in ['UL', 'UR', 'LL', 'LR']]
	
	if ul is None:
		ul = ur + ll - lr
	elif ll is None:
		ll = lr + ul - ur
	elif ur is None:
		ur = ul + lr - ll
	
	v10 = ur - ul
	v20 = ll - ul
	
	dx = v10 / int(dim.w)
	dy = v20 / int(dim.h)
	
	cur_y, cur = ul.copy(), ul.copy()
	
	w, h = int(texture.dim.w), int(texture.dim.h)
	res = np.ndarray((int(dim.h),int(dim.w)),dtype=np.uint32)
	res[:] = 0
	
	# below loop is optimized;
	# direct use of Point for maths here is apparently bad for performance
	cur_sx, cur_sy = ul.x, ul.y
	cur_x, cur_y = ul.x, ul.y
	dxx, dxy = dx.x, dx.y
	dyx, dyy = dy.x, dy.y
	for y in range(int(dim.h)):
		# cur = Point(cur_y.x, cur_y.y)
		cur_x, cur_y = cur_sx, cur_sy
		for x in range(int(dim.w)):
			# si = (int(cur.y) % h, int(cur.x) % w)
			si = (int(cur_y) % h, int(cur_x) % w)
			di = (y,x)
			res[di] = texture.data[si] 
			# cur += dx
			cur_x += dxx
			cur_y += dxy
		#cur_y += dy
		cur_sx += dyx
		cur_sy += dyy
	#return res
	res = res.reshape((int(dim.w)*int(dim.h),))
	texture = Texture(texture.key, dim, res)
	return texture


# def texture_region_to_rect(texture, poly, dim):
# """
# transforms a polygonal region of a texture to an upper-left right
# triangle
# """
# poly.verts[0] = poly.verts[0].vmul(texture.dim)
# poly.verts[1] = poly.verts[1].vmul(texture.dim)
# poly.verts[2] = poly.verts[2].vmul(texture.dim)
# v0,v1,v2 = poly.verts[0], poly.verts[1], poly.verts[2]
# v10, v21, v02 = v1 - v0, v2 - v1, v0 - v2


# mn = Point(int(min(min(v0.x,v1.x),v2.x)), int(min(min(v0.y,v1.y),v2.y)))
# mx = Point(int(max(max(v0.x,v1.x),v2.x)), int(max(max(v0.y,v1.y),v2.y)))
# mm = Point(mn.x,mx.y)
# det = Point((v0*v1).z,(v1*v2).z,(v2*v0).z)
# gabd = Point((v10*v2).z, (v21*v0).z, (v02*v1).z) + det
# gab = (Point((v10*mm).z, (v21*mm).z, (v02*mm).z) + det) / gabd
# abgd = Point(gabd.y, gabd.z, gabd.x)
# dy = Point(v10.y, v21.y, v02.y) / abgd
# dx = (Point(v10.x, v21.x, v02.x) / abgd) - (dy*(mx.x-mn.x))

# res = np.ndarray((int(dim.w),int(dim.h)), dtype=np.uint32)
# res[:] = 0
# for y in range(int(mx.y),int(mn.y),-1):
	# for x in range(int(mn.x),int(mx.x)):
		# if gab.x >= 0 and gab.y >= 0 and gab.z >= 0:
			# di = (int(gab.z*dim.h), int(gab.y*dim.w))
			# si = (y % int(texture.dim.h), x % int(texture.dim.w)) 
			# if di[0] >= dim.w or di[1] >= dim.h:
				# continue
			# res[di] = texture.data[si]
		# gab -= dy
	# gab -= dx
# #return res
# res = res.reshape((int(dim.w)*int(dim.h),))
# texture = Texture(texture.key, dim, res)
# return texture

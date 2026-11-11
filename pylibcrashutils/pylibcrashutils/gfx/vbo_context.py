from OpenGL.GL import *
from pylibcrashutils.gfx.gl import GLUTContext

import numpy as np

# glBufferData(GL_ARRAY_BUFFER, size, data, GL_STATIC_DRAW)
# - size = size of buffer in bytes
# - data = primitive buffer

# = size should be:   number of primitives 
#                   x size of primitive in floats/int32s 
#                   x 4 [bytes per float/int32]
#                   ------------------------------------
#                   = count x size x 4
# 
# glVertexPointer(coords, GL_FLOAT, byte_stride, None)
#
# - coords = number of coordinates to process per vertex
# - byte_stride = size of a vertex (coords data only) in bytes
# 
# = byte_stride should be:   number of coordinates actually in a vertex
#                          x 4 [bytes per float/int32/coordinate]
#                          --------------------------------------
#                          = 3x4 = 12
#
# glDrawArrays(gl_type, vert_offset, count)
#
# - count = number of vertices to draw; equivalent to count calls to 
#           glVertex3f in immediate mode 
# - vert_offset = offset of the first 'vertex', in units of 
#                 number of [float] coordinates actually in a vertex
#
#
# = we draw vertices in groups of the number of verts per primitive 
#   (i.e. 3 for polys, 4 for quads);

#   prims in memory are [
#                         [[(v1x,v1y,v1z),(v2x,v2y,v2z),(v3x,v3y,v3z)], 
#                          other data like uvws, texcoords] 
#                        x prim_count]
# 
#  that is, a single vertex is considered as just a point with 
#  positional coordinates, not including texcoords and other information
#  
#  there are 3 coordinates per Point structure, and thus 3 floats. 
#  size of primitive structures must therefore be aligned to 3 floats = 
#  12 bytes. if a primitive is 'viewed' as/casted to a Points array, 
#  then if will be consisted of 
#
#  size of primitive in floats/int32s / 3  = number of 'points' per primitive
#  
#  then the vert_offset is calculated as
#
#    primitive_idx  x  size of primitive in floats/int32s / 3
# 

# since the VBO layout is dependent on the geom structure layout
# this is broken out into a separate class 
class VBOContext(GLUTContext):
	
	# buffer = gl buffer object to use for primitive storage
	# stride = size of primitive in floats/int32s
	# count = number of vertices in primitive
	# gl_type = gl primitive type
	
	info = {
		'line': {
			'buffer': 'l_vbo',
			'stride': 6,  # (3 coords/point x 2 points)
			'count': 2,
			'gl_type': GL_LINES
		},
		'poly': {
			'buffer': 'p_vbo',
			'stride': 21,  # ((3 coords/vert x 3 verts) + (3 coords/uvw x 3 uvws) + 1 int32 texid + 2 int32 pad)
			'count': 3,
			'gl_type': GL_TRIANGLES,
			'idx_stride': 4,
			'idx_count': 3
		},
		'quad': {
			'buffer': 'q_vbo',
			'stride': 27,  # ((3 coords/vert x 4 verts) + (3 coords/uvw x 4 uvws) + 1 int32 texid + 2 int32 pad)
			'count': 4,
			'gl_type': GL_QUADS,
			'idx_stride': 4,
			'idx_count': 4
		}
	}
	
	
	def __init__(self, w, h, dimensions=2, indexed=False, colors_enabled=True):
		super().__init__(w,h)
		self.dimensions = dimensions
		self.indexed = indexed
		self.colors_enabled = colors_enabled
		if self.colors_enabled:
			glEnableClientState(GL_COLOR_ARRAY)
		self.counts = {}
		
	def init(self):
		super().init()
		self.init_vbos()

	def init_vbos(self):
		self.l_vbo = glGenBuffers(1)
		self.p_vbo = glGenBuffers(1)
		self.p_cbo = glGenBuffers(1)
		self.q_vbo = glGenBuffers(1)
		glEnableClientState(GL_VERTEX_ARRAY)
	
	color_buffer = np.ndarray((8192*16,),dtype=np.float32)
	def upload(self, kind, data):
		info = VBOContext.info[kind]
		count = len(data)
		self.counts[kind] = count
		vbo = getattr(self, info['buffer'])
		pt_count = info['count']
		stride = info['stride']
		glBindBuffer(GL_ARRAY_BUFFER, vbo)
		glBufferData(GL_ARRAY_BUFFER, count*stride*4, data, GL_STATIC_DRAW)
		glBindBuffer(GL_ARRAY_BUFFER, 0)
		if kind == 'poly' and self.colors_enabled:
			# adjust stride for colors
			stride = (stride // pt_count) * 3
			idx = 0
			for poly in data:
				for vert in poly.verts:
					VBOContext.color_buffer[idx] = vert.z/8192*2
					VBOContext.color_buffer[idx+1] = vert.z/8192*2
					VBOContext.color_buffer[idx+2] = vert.z/8192*2
					idx += 3
				idx += (stride - 9)
			glBindBuffer(GL_ARRAY_BUFFER, self.p_cbo)
			glBufferData(GL_ARRAY_BUFFER, count*stride*4, VBOContext.color_buffer, GL_STATIC_DRAW)
			glBindBuffer(GL_ARRAY_BUFFER, 0)

	def upload_lines(self, data):
		self.upload('line', data)
		
	def upload_polys(self, data):
		self.upload('poly', data)

	def upload_quads(self, data):
		self.upload('quad', data)
	
	def bind_vertex_pointer(self, kind):
		info = VBOContext.info[kind]
		if kind == 'line':
			stride = 0
		else:
			stride = info['stride']
		pt_count = info['count']
		vbo = getattr(self, info['buffer'])
		glBindBuffer(GL_ARRAY_BUFFER, vbo)
		glVertexPointer(self.dimensions, GL_FLOAT, 12, None)
		glBindBuffer(GL_ARRAY_BUFFER, 0)
		if kind=='poly' and self.colors_enabled:
			cbo = self.p_cbo
			glBindBuffer(GL_ARRAY_BUFFER, cbo)
			glColorPointer(3, GL_FLOAT, 12, None)
			glBindBuffer(GL_ARRAY_BUFFER, 0)
			
	def draw_prims(self, kind, data=None, wireframe=False):
		if data is not None:
			self.upload(kind, data)
		count = self.counts.get(kind)
		info = VBOContext.info[kind]
		vbo = getattr(self, info['buffer'])
		gl_type = info['gl_type']
		pt_count = info['count']
		stride = info['stride'] // 3
		#glPolygonMode( GL_FRONT_AND_BACK, GL_LINE )
		#glBindBuffer(GL_ARRAY_BUFFER, vbo)
		self.bind_vertex_pointer(kind)
		glBindBuffer(GL_ARRAY_BUFFER, vbo)
		if wireframe == False or kind == 'line':
			if self.indexed:
				glDrawElements(gl_type, count*pt_count, GL_UNSIGNED_INT, None)
			else:
				for idx in range(count):
					glDrawArrays(gl_type, idx*stride, pt_count)
		else:
			if self.indexed:
				idx_stride = info['idx_stride']
				idx_count = info['idx_count']
				for idx in range(quad_count):
					rng = (idx_stride*idx, idx_stride*idx+idx_count)
					glDrawElements(GL_LINE_LOOP, 3, GL_UNSIGNED_INT,
						(c_int*idx_count)(*list(range(*rng))))
			else:
				for idx in range(count):
					glDrawArrays(GL_LINE_LOOP, idx*stride, pt_count)
		glBindBuffer(GL_ARRAY_BUFFER, 0)
		
	def draw_prims_wireframe(self, kind, data=None):
		self.draw_prims(kind, data, True)
		
	def draw_lines(self, data=None):
		self.draw_prims('line', data, False)
		
	def draw_lines_wireframe(self, data=None):
		self.draw_prims('line', data, True)

	def draw_polys(self, data=None):
		self.draw_prims('poly', data, False)
		
	def draw_polys_wireframe(self, data=None):
		self.draw_prims('poly', data, True)
		
	def draw_quads(self, data=None):
		self.draw_prims('quad', data, False)
		
	def draw_quads_wireframe(self, data=None):
		self.draw_prims('quad', data, True)
		
	def flush(self):
		glFlush()

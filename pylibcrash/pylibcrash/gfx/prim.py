import numpy as np

# wrappers for the primitive structs in gfx.h

# these are actually wrappers around numpy structured arrays with
# the same memory layouts as the gfx.h structs (rather than cffi objects) 
# these can easily be 'casted' to and from arrays of primitive c type 
# for interfacing with c code as well as pyopengl, without the need for
# otherwise expensive copying of data into new python objects

class Point(np.void):
	dtype = np.dtype([('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
	def __new__(cls, x, y, z=0.0):
		rec = np.array([(x,y,z)], dtype=cls)[0]
		return rec
		
	@property
	def x(self):
		return self['x']
		
	@x.setter
	def x(self, value):
		self['x'] = value
		
	@property
	def y(self):
		return self['y']
		
	@y.setter
	def y(self, value):
		self['y'] = value
		
	@property
	def z(self):
		return self['z']
	
	@z.setter
	def z(self, value):
		self['z'] = value

class Texcoord(np.void):
	dtype = np.dtype([('u', 'f4'), ('v', 'f4'), ('w', 'f4')])
	def __new__(cls, u, v, w=1.0):
		rec = np.array([(u,v,w)], dtype=cls)[0]
		return rec

	@property
	def u(self):
		return self['u']
	
	@u.setter
	def u(self, value):
		self['u'] = value
		
	@property
	def v(self):
		return self['v']
	
	@v.setter
	def v(self, value):
		self['v'] = value

	@property
	def w(self):
		return self['w']
	
	@w.setter
	def w(self, value):
		self['w'] = value

class Poly(np.void):
	dtype = np.dtype([('verts', Point, (3,)), 
					  ('vertuvws', Texcoord, (3,)),
					  ('texid', np.int32),
					  ('pad1', np.int32), ('pad2', np.int32)])
	def __new__(cls, verts, vertuvws=None, texid=-1):
		if vertuvws is None:
			vertuvws = np.array([0,0,1]*3, dtype=Texcoord)
		rec = np.array([(verts, vertuvws, texid, 0, 0)], dtype=cls)[0]
		return rec
		
	@property
	def verts(self):
		return self['verts']
		
	@verts.setter
	def verts(self, verts):
		self['verts'] = verts
		
	@property
	def vertuvws(self):
		return self['vertuvws']
			
	@vertuvws.setter
	def vertuvws(self, vertuvws):
		self['vertuvws'] = vertuvws
		
	@property
	def texid(self):
		return self['texid']
			
	@texid.setter
	def texid(self, texid):
		self['texid'] = texid
		
class Quad(np.void):
	dtype = np.dtype([('verts', Point, (4,)), 
					  ('vertuvws', Texcoord, (4,)),
					  ('texid', np.int32),
					  ('pad1', np.int32), ('pad2', np.int32)])
	def __new__(cls, verts, vertuvws=None, texid=-1):
		if vertuvws is None:
			vertuvws = np.array([0,0,1]*4, dtype=Texcoord)
		rec = np.array([(verts, vertuvws, texid, 0, 0)], dtype=cls)[0]
		return rec
		
	@property
	def verts(self):
		return self['verts']
		
	@verts.setter
	def verts(self, verts):
		self['verts'] = verts
		
	@property
	def vertuvws(self):
		return self['vertuvws']
			
	@vertuvws.setter
	def vertuvws(self, vertuvws):
		self['vertuvws'] = vertuvws
		
	@property
	def texid(self):
		return self['texid']
			
	@vertuvws.setter
	def texid(self, texid):
		self['texid'] = texid
	
class Vector(Point):
	pass
	
class Angle(Point):
	pass

class Line(np.void):
	dtype = np.dtype([('points', Point, (2,))])
	def __new__(cls, points):
		rec = np.array([(points,)], dtype=cls)[0]
		return rec
		
	@property
	def points(self):
		return self['points']
		
	@points.setter
	def points(self, points):
		self['points'] = points
		
class Rect3d:
	def __init__(self, loc, dim):
		self.loc = loc
		self.dim = dim
	
	@property
	def quads(self):
		loc_arr = [self.loc.x,self.loc.y,self.loc.z]
		dim_arr = [self.dim.w,self.dim.h,self.dim.d]
		
		face_idxs = [(idx,p) for idx in [0,1,2] for p in [0,1]]
		quads = []
		for idx,p in face_idxs:
			verts = []
			for xy in [[0,0],[1,0],[1,1],[0,1]]:
				xyz = xy[:idx]+[p]+xy[idx:]
				comps = [loc_arr[i]+(dim_arr[i]*xyz[i]) for i in range(3)]
				point = Point(*comps)
				verts.append(point)
			quad = Quad(verts, [1,1,1,1])
			quads.append(quad)
		return quads

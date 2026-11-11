from math import *

import numpy as np
import pylibcrash.gfx.prim

class Point(pylibcrash.gfx.prim.Point):
	def __init__(self, x, y, z=0):
		self.x = x
		self.y = y
		self.z = z

	@staticmethod
	def from_list(lst):
		return Point(lst[0], lst[1], lst[2])

	def copy(self):
		return Point(self.x, self.y, self.z)
	
	def __iter__(self):
		yield self.x
		yield self.y
		yield self.z
		
	def __add__(self, other):
		x = self.x + other.x
		y = self.y + other.y
		z = self.z + other.z
		return self.__class__(x, y, z)

	def __radd__(self, other):
		self.__add__(other)

	def __sub__(self, other):
		x = self.x - other.x
		y = self.y - other.y
		z = self.z - other.z
		return self.__class__(x, y, z)

	def __rsub__(self, other):
		return self.__class__.__sub__(other, self)

	def __mul__(self, other):
		if isinstance(other, self.__class__):
			p1 = self
			p2 = other
			x = p1.y * p2.z - p1.z * p2.y
			y = p1.z * p2.x - p1.x * p2.z
			z = p1.x * p2.y - p1.y * p2.x
		else:
			x = self.x * other
			y = self.y * other
			z = self.z * other
		return self.__class__(x, y, z)

	def __rmul__(self, other):
		return self.__class__.__mul__(other, self)

	def __pow__(self, other):
		p1 = self
		p2 = other
		return p1.x * p2.x + p1.y * p2.y + p1.z * p2.z

	def __rpow__(self, other):
		return self.__class__.__pow__(other, self)

	def __neg__(self):
		return self.__class__(-self.x, -self.y, -self.z)

	def __divmod__(self, other):
		if isinstance(other, self.__class__):
			return self.__class__(self.x // other.x, self.y // other.y,
								  self.z // other.z), \
				   self.__class__(self.x % other.x, self.y % other.y, self.z % other.z)
		else:
			return self.__class__(self.x // other, self.y // other, self.z // other), \
				   self.__class__(self.x % other, self.y % other, self.z % other)

	def __floordiv__(self, other):
		if isinstance(other, self.__class__):
			return self.__class__(self.x // other.x, self.y // other.y,
								  self.z // other.z)
		else:
			return self.__class__(self.x // other, self.y // other, self.z // other)

	def __truediv__(self, other):
		if isinstance(other, self.__class__):
			return self.__class__(self.x / other.x, self.y / other.y, self.z / other.z)
		else:
			return self.__class__(self.x / other, self.y / other, self.z / other)

	def vmul(self, other):
		return self.__class__(self.x * other.x, self.y * other.y, self.z * other.z)

	def __hash__(self):
		return hash((self.x, self.y, self.z))

	def __eq__(self, other):
		return self.x == other.x and self.y == other.y and self.z == other.z
		
	def denormalize(self, dim):
		return (self + Point(1,1,1)).vmul(dim) / 2
		
	def normalize(self, dim):
		if dim.z == 0:
			dim = Dimensions(dim.x, dim.y, 1)
		return ((self / dim) * 2) - Point(1,1,1)
		
	def pad_rect3d(self, dim):
		p1 = Point(self.x - (dim.w / 2), self.y - (dim.h / 2), self.z - (dim.d / 2))
		rect = Rect3d(p1, dim)
		return rect

		
class Vector(Point):
	def __init__(self, x, y, z):
		super().__init__(x, y, z)

	@staticmethod
	def from_point(point):
		return Vector(point.x, point.y, point.z)

	def to_point(self):
		return Point(self.x, self.y, self.z)
		
	def magnitude(self):
		mag = sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
		return mag
		
	def normalize(self):
		mag = self.magnitude()
		return Vector(self.x / mag, self.y / mag, self.z / mag)

	def angle(self, other):
		# by definition of dot product
		n1 = self.normalize()
		n2 = other.normalize()
		angle = acos(n1 ** n2)
		return angle
		
# euler/tait-bryan angle
class Angle(Vector):
	
	@staticmethod
	def from_axis_angle(axis, angle, order='ZXY'):
		nc = 1-cos(angle)
		x,y,z = tuple(axis)
		if order == 'ZXY': 
			m21 = y*z*nc - x*sin(angle)
			x = asin(m21)
			if abs(m21) > 0.99998: # singularity
				y = 0
				z = atan2(z*sin(angle)+x*y*nc, 1-(y**2 + z**2)*nc)
			else:
				y = atan2(y*sin(angle)-x*z*nc, 1-(x**2 + y**2)*nc)
				z = atan2(z*sin(angle)-x*y*nc, 1-(x**2 + z**2)*nc)
			return Angle(x,y,z)
		else:
			raise Exception("not implemented")
			
	@staticmethod
	def from_vec(vec, order='ZXY'):
		zdir = abs(vec.z)/vec.z
		axis = Vector(-vec.y,vec.x,0)*zdir
		angle = vec.angle(Vector(0,0,zdir))
		return Angle.from_axis_angle(axis, angle, order)
		
class Dimensions(Point):
	def __init__(self, w, h, d=0):
		super().__init__(w, h, d)
	
	def copy(self):
		return Dimensions(self.w, self.h, self.d)
		
	@property
	def w(self):
		return self.x
	@w.setter
	def w(self, value):
		self.x = value
	@property
	def h(self):
		return self.y
	@h.setter
	def h(self, value):
		self.y = value
	@property
	def d(self):
		return self.z
	@d.setter
	def d(self, value):
		self.z = value

	@staticmethod
	def from_vec(vec):
		return Dimensions(vec.x, vec.y, vec.z)

	@staticmethod
	def from_point(point):
		return Dimensions(point.x, point.y, point.z)
		
	def to_vec(self):
		return Vector(self.w, self.h, self.d)

	def to_point(self):
		return Point(self.w, self.h, self.d)

class Rect2d:
	def __init__(self, loc, dim):
		self.loc = loc
		self.dim = dim

	def copy(self):
		return Rect2d(self.loc.copy(), self.dim.copy())
		
	def to_quad(self):
		quad = Quad([Point(self.loc.x, self.loc.y),
					 Point(self.loc.x + self.dim.w, self.loc.y),
					 Point(self.loc.x + self.dim.w, self.loc.y + self.dim.h),
					 Point(self.loc.x, self.loc.y + self.dim.h)])
		return quad
		
	@property
	def verts(self):
		return self.to_quad().verts
		
	@property
	def edges(self):
		return self.to_quad().edges
	
	@property
	def center(self):
		return Point(self.loc.x + (self.dim.w / 2),
					 self.loc.y + (self.dim.h / 2))
	
	@property
	def p1(self):
		return self.loc
		
	@p1.setter
	def p1(self, value):
		self.loc = p1
		
	@property
	def p2(self):
		return Point(self.loc.x + self.dim.w, self.loc.y + self.dim.h)
	
	@p2.setter
	def p2(self, value):
		self.dim.w = value.x - self.loc.x
		self.dim.h = value.y - self.loc.y
	
	@property
	def ul(self):
		return self.loc
		
	@property
	def ur(self):
		return self.loc + Point(self.dim.w, 0)
	
	@property
	def ll(self):
		return self.loc + Point(0, self.dim.h)
	
	@property
	def lr(self):
		return self.loc + self.dim
		
	def find_rect2d_intersection(self, rect):
		p1,p2 = Point(0,0), Point(0,0)
		if self.p2.x == rect.p1.x:
			return self.edges[1].find_line_intersection(rect.edges[3])
		elif self.p1.x == rect.p2.x:
			return self.edges[3].find_line_intersection(rect.edges[1])
		elif self.p2.y == rect.p1.y:
			return self.edges[2].find_line_intersection(rect.edges[0])
		elif self.p1.y == rect.p2.y:
			return self.edges[0].find_line_intersection(rect.edges[2])
		if self.p2.x < rect.p1.x:
			return None
		if self.p1.x > rect.p2.x:
			return None
		if self.p2.y < rect.p1.y:
			return None
		if self.p1.y < rect.p2.y:
			return None
		p1.x = max(self.p1.x, rect.p1.x)
		p2.x = min(self.p2.x, rect.p2.x)
		p1.y = max(self.p1.y, rect.p1.y)
		p2.y = min(self.p2.y, rect.p2.y)
		rect = Rect2d(p1, Dimensions.from_vec(p2-p1))
		return rect

	def find_point_inside(self, point):
		if self.loc.x <= point.x <= self.loc.x + self.dim.w \
				and self.loc.y <= point.y <= self.loc.y + self.dim.h:
			return point
		return None
		
	
		
class Face(Rect2d):
	def __init__(self, loc, dim, plane, offset):
		super().__init__(loc, dim)
		self.plane = plane
		self.offset = offset
		
	def to_quad(self):
		if self.plane == 'xy':
			quad = Quad([Point(self.loc.x, self.loc.y, self.offset),
						 Point(self.loc.x + self.dim.w, self.loc.y, self.offset),
						 Point(self.loc.x + self.dim.w, self.loc.y + self.dim.h,
							   self.offset),
						 Point(self.loc.x, self.loc.y + self.dim.h, self.offset)])
		elif self.plane == 'xz':
			quad = Quad([Point(self.loc.x, self.offset, self.loc.y),
						 Point(self.loc.x + self.dim.w, self.offset, self.loc.y),
						 Point(self.loc.x + self.dim.w, self.offset,
							   self.loc.y + self.dim.h),
						 Point(self.loc.x, self.offset, self.loc.y + self.dim.h)])
		elif self.plane == 'yz':
			quad = Quad([Point(self.offset, self.loc.x, self.loc.y),
						 Point(self.offset, self.loc.x + self.dim.w, self.loc.y),
						 Point(self.offset, self.loc.x + self.dim.w,
							   self.loc.y + self.dim.h),
						 Point(self.offset, self.loc.x, self.loc.y + self.dim.h)])
		return quad

	def find_line_intersection(self, line):
		if self.plane == 'xy':
			if line.points[1].z - line.points[0].z == 0:
				return None
			t = (self.offset - line.points[0].z) / (line.points[1].z - line.points[0].z)
			if not 0 <= t <= 1:
				return None
			x = line.points[0].x + t * (line.points[1].x - line.points[0].x)
			y = line.points[0].y + t * (line.points[1].y - line.points[0].y)
			if self.loc.x <= x <= self.loc.x + self.dim.w \
					and self.loc.y <= y <= self.loc.y + self.dim.h:
				return Point(x, y, self.offset)
		elif self.plane == 'xz':
			if line.points[1].y - line.points[0].y == 0:
				return None
			t = (self.offset - line.points[0].y) / (line.points[1].y - line.points[0].y)
			if not 0 <= t <= 1:
				return None
			x = line.points[0].x + t * (line.points[1].x - line.points[0].x)
			z = line.points[0].z + t * (line.points[1].z - line.points[0].z)
			if self.loc.x <= x <= self.loc.x + self.dim.w \
					and self.loc.y <= z <= self.loc.y + self.dim.h:
				return Point(x, self.offset, z)
		elif self.plane == 'yz':
			if line.points[1].x - line.points[0].x == 0:
				return None
			t = (self.offset - line.points[0].x) / (line.points[1].x - line.points[0].x)
			if not 0 <= t <= 1:
				return None
			y = line.points[0].y + t * (line.points[1].y - line.points[0].y)
			z = line.points[0].z + t * (line.points[1].z - line.points[0].z)
			if self.loc.x <= y <= self.loc.x + self.dim.w \
					and self.loc.y <= z <= self.loc.y + self.dim.h:
				return Point(self.offset, y, z)
		return None
		
class Rect3d(pylibcrash.gfx.prim.Rect3d):
	def __init__(self, loc, dim):
		self.loc = loc
		self.dim = dim

	def get_faces(self):
		faces = [Face(Point(self.loc.x, self.loc.y),
					  Dimensions(self.dim.w, self.dim.h),
					  'xy', self.loc.z),
				 Face(Point(self.loc.x, self.loc.y),
					  Dimensions(self.dim.w, self.dim.h),
					  'xy', self.loc.z + self.dim.d),
				 Face(Point(self.loc.x, self.loc.z),
					  Dimensions(self.dim.w, self.dim.d),
					  'xz', self.loc.y),
				 Face(Point(self.loc.x, self.loc.z),
					  Dimensions(self.dim.w, self.dim.d),
					  'xz', self.loc.y + self.dim.h),
				 Face(Point(self.loc.y, self.loc.z),
					  Dimensions(self.dim.h, self.dim.d),
					  'yz', self.loc.x),
				 Face(Point(self.loc.y, self.loc.z),
					  Dimensions(self.dim.h, self.dim.d),
					  'yz', self.loc.x + self.dim.w)]
		return faces

	def find_line_intersection(self, line):
		faces = self.get_faces()
		for face in faces:
			intersection = face.find_line_intersection(line)
			if intersection:
				return intersection
		return None

	def find_poly_intersection(self, poly):
		faces = self.get_faces()
		edges = poly.get_edges()
		for edge in edges:
			intersection = self.find_line_intersection(edge)
			if intersection:
				return intersection
		edges = sum([face.to_quad().get_edges() for face in faces], [])
		for edge in edges:
			intersection = poly.find_line_intersection(edge)
			if intersection:
				return intersection
		return None

	def find_point_inside(self, point):
		if self.loc.x <= point.x <= self.loc.x + self.dim.w \
				and self.loc.y <= point.y <= self.loc.y + self.dim.h \
				and self.loc.z <= point.z <= self.loc.z + self.dim.d:
			return point
		return None

	def find_line_point_inside(self, line):
		for point in line.points:
			point = self.find_point_inside(point)
			if point:
				return point
		return None

	def find_poly_vert_inside(self, poly):
		for vert in poly.verts:
			vert = self.find_point_inside(vert)
			if vert:
				return vert
		return None

	def find_line_collision(self, line):
		point = self.find_line_point_inside(line)
		if point:
			return point
		point = self.find_line_intersection(line)
		return point

	def find_poly_collision(self, poly):
		vert = self.find_poly_vert_inside(poly)
		if vert:
			return vert
		point = self.find_poly_intersection(poly)
		return point

	def find_rect3d_collision(self, rect3d):
		if self.loc.x < rect3d.loc.x and \
		   self.loc.x + self.dim.w < rect3d.loc.x:
			return None
		if self.loc.x > rect3d.loc.x + rect3d.dim.w and \
		   self.loc.x + self.dim.w > rect3d.loc.x + rect3d.dim.w:
			return None
		if self.loc.y < rect3d.loc.y and \
		   self.loc.y + self.dim.h < rect3d.loc.y:
			return None
		if self.loc.y > rect3d.loc.y + rect3d.dim.h and \
		   self.loc.y + self.dim.h > rect3d.loc.y + rect3d.dim.h:
			return None
		if self.loc.z < rect3d.loc.z and \
		   self.loc.z + self.dim.d < rect3d.loc.z:
			return None
		if self.loc.z > rect3d.loc.z + rect3d.dim.d and \
		   self.loc.z + self.dim.d > rect3d.loc.z + rect3d.dim.d:
			return None
			
		loc = Point(max([self.loc.x, rect3d.loc.x]), 
					max([self.loc.y, rect3d.loc.y]),
					max([self.loc.z, rect3d.loc.z]))
		loc2 = Point(min([self.loc.x+self.dim.w, rect3d.loc.x+rect3d.dim.w]),
					 min([self.loc.y+self.dim.h, rect3d.loc.y+rect3d.dim.h]),
					 min([self.loc.z+self.dim.d, rect3d.loc.z+rect3d.dim.d]))
		dim = Dimensions.from_vec(loc2 - loc)
		
		dim_array = [dim.w, dim.h, dim.d]
		col_type = len([val for val in dim_array if val != 0])
		if col_type == 3:
			collision = Rect3d(loc, dim)
		elif col_type == 2:
			idx = dim_array.index(0)
			rect = list(zip([loc.x,loc.y,loc.z],[dim.w,dim.h,dim.d]))
			offset = rect.pop(idx)[0]
			plane = ['yz','xz','xy'][idx]
			loc = Point(rect[0][0],rect[1][0])
			dim = Dimensions(rect[0][1],rect[1][1])
			collision = Face(loc, dim, plane, offset)
		elif col_type == 1:
			collision = Line([loc,loc+dim])
		elif col_type == 0:
			collision = loc
		return collision
		
	def pad_rect3d(self, dim):
		p1 = Point(self.loc.x - (dim.w / 2), self.loc.y - (dim.h / 2), self.loc.z - (dim.d / 2))
		dim = Dimensions.from_vec(dim.to_vec() + self.dim.to_vec())
		rect3d = Rect3d(p1, dim)
		return rect3d

	@property
	def center(self):
		center = Point(self.loc.x + (self.dim.w / 2), 
					   self.loc.y + (self.dim.h / 2),
					   self.loc.z + (self.dim.d / 2))
		return center
		
	@property
	def p1(self):
		return self.loc
		
	@p1.setter
	def p1(self, value):
		self.loc = p1
	
	@property
	def p2(self):
		p2 = Point(self.loc.x + self.dim.w, \
				   self.loc.y + self.dim.h, \
				   self.loc.z + self.dim.d)
		return p2

	@p2.setter
	def p2(self, value):
		self.dim.w = value.x - self.loc.x
		self.dim.h = value.y - self.loc.y
		self.dim.d = value.z - self.loc.z

class Line(pylibcrash.gfx.prim.Line):
	dtype = np.dtype([('points', Point, (2,))])
	def __init__(self, points):
		self.points = points

	@staticmethod
	def from_vec(vec, origin):
		return Line([origin, origin + vec])

	def to_vec(self):
		return Vector.from_point(self.points[1] - self.points[0])
		
	@property
	def center(self):
		return sum(self.points)/2
		
	def lerp(self, t):
		return self.points[0] + (self.points[1] - self.points[0])*t

	def antilerp(self, point):
		d = self.points[1] - self.points[0]
		dp = point - self.points[0]
		if d.x == 0: d.x = 0.0001
		if d.y == 0: d.y = 0.0001
		if d.z == 0: d.z = 0.0001
		t = dp / d
		return t
	
	def find_line_intersection(self, line):
		d1 = self.to_vec()
		d2 = line.to_vec()
		if d2.x*d1.y - d2.y*d1.x == 0:
			points = set()
			p00,p01 = self.points
			p10,p11 = line.points
			tests = [(p00, line), (p01, line), (p10, self), (p11, self)]
			for test in tests:
				t = test[1].antilerp(test[0])[0]
				if 0 <= t <= 1 and test[0].y == test[1].lerp(t).y:
					points.add(test[0])
			if len(points) == 0:
				return None
			if len(points) == 1:
				return points[0]
			return Line(list(points))
		dc = line.points[0] - self.points[0]
		t = (dc.y*d1.x - dc.x*d1.y)/(d2.x*d1.y - d2.y*d1.x)
		if not 0 <= t <= 1:
			return None
		return line.lerp(t)
		
class Texcoord(pylibcrash.gfx.prim.Texcoord):
	dtype = np.dtype([('u', 'f4'), ('v', 'f4'), ('w', 'f4')])
	def __new__(cls, u, v, w=1.0):
		rec = np.array([(u,v,w)], dtype=cls)[0]
		return rec
		
class Poly(pylibcrash.gfx.prim.Poly):
	dtype = np.dtype([('verts', Point, (3,)), 
					  ('vertuvws', Texcoord, (3,)),
					  ('texid', np.int32),
					  ('pad1', np.int32), ('pad2', np.int32)])
	def __new__(cls, verts, vertuvws=None, texid=-1):
		if vertuvws is None:
			vertuvws = np.array([Texcoord(0,0)]*3)
		rec = np.array([(verts, vertuvws, texid, 0, 0)], dtype=cls)[0]
		return rec

	def get_edges(self):
		edges = [Line([self.verts[0], self.verts[1]]),
				 Line([self.verts[1], self.verts[2]]),
				 Line([self.verts[2], self.verts[0]])]
		return edges

	def find_line_intersection(self, line):
		edges = self.get_edges()
		cross = line.to_vec() * -edges[2].to_vec()
		det = edges[0].to_vec() ** cross
		if det == 0:
			return None
		tvec = line.points[0] - self.verts[0]
		u = (tvec ** cross) * (1 / det)
		if not 0 <= u <= 1:
			return None
		qvec = tvec * edges[0].to_vec()
		v = (line.to_vec() ** qvec) * (1 / det)
		if v < 0 or u + v > 1:
			return None
		t = (-edges[2].to_vec() ** qvec) * (1 / det)
		if not 0 <= t <= 1:
			return None
		p = self.verts[0] + \
			edges[0].to_vec() * u - edges[2].to_vec() * v
		return p


class Quad(np.void):
	dtype = np.dtype([('verts', Point, (4,)), 
					  ('vertuvws', Texcoord, (4,)),
					  ('texid', np.int32),
					  ('pad1', np.int32), ('pad2', np.int32)])
	def __new__(cls, verts, vertuvws=None, texid=-1):
		if vertuvws is None:
			vertuvws = np.array([Texcoord(0,0)]*4)
		rec = np.array([(verts, vertuvws, texid, 0, 0)], dtype=cls)[0]
		return rec
	
	def __init__(self, verts):
		self.verts = verts

	def get_edges(self):
		edges = [Line([self.verts[0], self.verts[1]]),
				 Line([self.verts[1], self.verts[2]]),
				 Line([self.verts[2], self.verts[3]]),
				 Line([self.verts[3], self.verts[0]])]
		return edges

	@property
	def center(self):
		return sum(self.verts, Point(0,0,0))/4

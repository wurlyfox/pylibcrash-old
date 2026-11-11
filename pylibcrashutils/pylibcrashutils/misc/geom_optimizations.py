import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')

from pylibcrashutils.gfx.vbo_context import VBOContext
from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.general.geom_comp import *

from OpenGL.GL import *
from OpenGL.GLU import *

import numpy as np
from datetime import datetime


def product(*args, repeat=1):
    pools = [tuple(pool) for pool in args] * repeat
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)

def subarray(array, slices):
	slc = slices[0]
	if not isinstance(slc, slice):
		slc = slice(*slc)
	if len(slices) > 1:
		return [subarray(item, slices[1:]) for item in array[slc]]
	else:
		return array[slc]
	
def test_rasterize_3d():
	polys = [random_poly() for _ in range(50)]
	
	bound = Rect3d(Point(-100, -100, -100), Dimensions(200, 200, 200))
	res = rasterize_3d(polys, bound, res=[6,6,6], face_res=[10,10,10])
	
	octree = pixels_3d_to_octree(res, bound)
	print(octree)
	

def rasterize_3d(polys, bound=None, res=None, face_res=None):
	if res is None:
		res = [3,3,3]
	if face_res is None:
		face_res = [3,3]
	res = Dimensions(2**res[0], 2**res[1], 2**res[2])
	face_res = Dimensions(2**face_res[0], 2**face_res[1])
	
	if bound is None:
		bound = get_polys_bound(polys)

	dim = bound.dim / res
	cols = [[[0 for _ in range(int(res.d))] 
				for __ in range(int(res.h))] 
				for ___ in range(int(res.w))]
	
	for poly in polys:
		v0, v1, v2 = poly.verts
		v0 = ((v0 - bound.loc) / bound.dim).vmul(res)
		v1 = ((v1 - bound.loc) / bound.dim).vmul(res)
		v2 = ((v2 - bound.loc) / bound.dim).vmul(res)
		edges = [v1-v0, v2-v0]
		deltas = [edges[i] / face_res[i] for i in range(2)]
		cur, cur2 = v0.copy(), v0.copy()
		for s in range(int(face_res[0])):
			cur = cur2
			for t in range(s,int(face_res[1])):
				cur += deltas[0]
				cols[int(cur.x)][int(cur.y)][int(cur.z)] = 1
			cur2 += deltas[1]
	return cols
	

def flatten(lst):
	res = []
	for item in lst:
		if isinstance(item, list):
			res.extend(flatten(item))
		else:
			res.append(item)
	return res
	
def pixels_3d_to_octree(array, bound):
	dim = bound.dim / 2
	shape = (len(array), len(array[0]), len(array[0][0]))
	part = tuple([1 if s == 1 else s // 2 for s in shape])
	times = tuple([1 if s == 1 else 2 for s in shape])
	ranges = product(*[range(time) for time in times]) 
	res = []
	for rng in ranges:
		slices = [(rng[i]*part[i], (rng[i]+1)*part[i]) for i in range(3)]
		sub = subarray(array, slices)
		flatsub = flatten(sub)
		mult = Dimensions(*rng)
		new_bound = Rect3d(bound.loc+(dim.vmul(mult)), dim)
		if all(s == 1 for s in flatsub):
			res.append(new_bound)
		elif any(s == 1 for s in flatsub):
			res.append(pixels_3d_to_octree(sub, new_bound))
		else:
			res.append(None)
	return res
	
def random_point(size=100, normalize=True):
	coords = tuple([random.randint(-size, size) for _ in range(3)])
	point = Point(*coords)
	if normalize == True:
		point /= size
	return point
	
def random_poly(size=100, normalize=True):
	verts = [random_point(size, normalize) for _ in range(3)]
	poly = Poly(verts)
	return poly

class Context(VBOContext):
	def __init__(self, w, h, dimensions=3):
		super().__init__(w, h, dimensions=dimensions, colors_enabled=False)
		# initialize global primitive buffers here
		# also any non-dynamic primitive buffers should be uploaded here
		# with self.upload_<prim_type>(data)
		self.polys = np.array([random_poly() for _ in range(250)])
		self.upload_polys(self.polys)
		self.init_octree(self.polys)
		self.rot = 0
		
	def init_octree(self, polys):
		bound = Rect3d(Point(-1.5,-1.5,-1.5), Dimensions(3.0,3.0,3.0))
		
		t1 = datetime.now()
		pixels = rasterize_3d(polys, bound, res=Dimensions(3,3,3), 
											face_res=Dimensions(3,3,3))
		#bound = Rect3d(Point(-0.75,-0.5,-0.5), Dimensions(2.0,2.0,2.0))
		self.octree = pixels_3d_to_octree(pixels, bound)
		t1 = datetime.now() - t1
		t2 = datetime.now()
		tree2 = generate_octree(polys, bound, [2,2,2])
		t2 = datetime.now() - t2
		print(t1, t2)
		self.quads = np.array([face.to_quad() 
					  for rect in flatten(tree2)
					  if rect is not None
					  for face in rect.get_faces()])
		self.upload_quads(self.quads)
		
		
		
	def draw(self):
		self.update()
		gluPerspective(45, self.w/self.h, 0.01, 10000.0)
		# do drawing code here
		# use self.draw_<prim_type>s([data]) passing optional data arg 
		# if prims are dynamic 
		glTranslatef(0.0,0.0,-5.0)
		glRotatef(self.rot,1.0,1.0,0.0)
		glColor3f(1.0,1.0,1.0)
		self.draw_polys_wireframe(self.polys)
		self.draw_quads_wireframe(self.quads)
		self.flush()
		
	def update(self):
		# do non-graphical updating logic here
		self.rot += 1
		
	def keys(self, key, x, y):
		# handle keys here
		pass
		
def main():
	dim = Dimensions(640, 480)
	context = Context(dim.w, dim.h)
	context.loop()
		
if __name__ == '__main__':
	main()

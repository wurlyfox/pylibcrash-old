import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')

from libcrash import lib, ffi

from pylibcrash.nsd import Nsd
from pylibcrash.nsf import Nsf
from pylibcrash.page import Page, TexturePage
from pylibcrash.entry import Entry, Eid #, Item
from pylibcrash.formats.zdat import Zone

from pylibcrashutils.gfx.scene import Scene
from pylibcrashutils.gfx.vbo_context import VBOContext
from pylibcrashutils.gfx.general.geom import *

from pylibcrash.formats.slst import PolyId
from pylibcrashutils.gfx.rasterize import clip_polys

from pylibcrashutils.gfx.gl.util import GLCamera

from OpenGL.GL import *
from OpenGL.GLU import *

import numpy as np

def build_frustum(dim, near, far):
	
	# near face is from (-dim.w/2, -dim.h/2, near) - (dim.w/2, dim.h/2, near)
	# far face is from near_face*(far/near)
	rect = Rect2d(-dim/2, dim)
	fdim = dim*(far/near)
	frect = Rect2d(-fdim/2, fdim)
	
	nul,nur,nll,nlr = [c+Point(0,0,near) for c in [rect.ul,rect.ur,rect.ll,rect.lr]]
	ful,fur,fll,flr = [c+Point(0,0,far) for c in [frect.ul,frect.ur,frect.ll,frect.lr]]
	
	lquad = Quad([nul, ful, fll, nll])
	rquad = Quad([nur, fur, flr, nlr])
	tquad = Quad([nul, ful, fur, nur])
	bquad = Quad([nll, fll, flr, nlr])
	nquad = Quad([nul, nur, nlr, nll])
	fquad = Quad([ful, fur, flr, fll])
	
	# nll-nul = (0,rect.dim.h,0)
	# nll-fll = (-rect.dim.w*((far/near)-1)/2, -rect.dim.h*((far/near)-1)/2, far-near)
	
	depth = far-near
	scale = ((far/near)-1)/(2*depth)
	quads = [lquad,rquad,tquad,bquad,nquad,fquad]
	z1 = -(rect.dim.w*scale)
	z2 = -(rect.dim.h*scale)
	
	
	normals = [Vector(-1, 0, z1)*depth, 
			   Vector(1, 0, z1)*depth,
			   Vector(0, -1, z2)*depth,
			   Vector(0, 1, z2)*depth,
			   Vector(0,0,-rect.dim.w/rect.dim.h)*depth, 
			   Vector(0,0,rect.dim.w/rect.dim.h)*depth]
	
	normals2 = [Vector(0,0,0),
	            Vector(0,0,0),
	            (nur-nul)*(ful-nul)]
	
	lines = [Line.from_vec(normal, sum(quad.verts, Point(0,0,0))/4)
	         for normal, quad in zip(normals, quads)] \
	      + [Line.from_vec(normal, sum(quad.verts, Point(0,0,0))/4)
	         for normal, quad in zip(normals2, quads)]
	                  
	quads = np.array(quads, dtype=Quad)
	lines = np.array(lines, dtype=Line)
	return quads, lines
	
def pack_bits(bool_list):
	res = 0
	tmp = [res := (res << 1) | int(b) for b in bool_list]
	return res
	
tmp_id = 0

def face_intersection(poly, segment, face, rect, near, far):
	depth = far - near
	scale = ((far/near)-1)/(2*depth)
	
	line = Line([poly.verts[segment[0]], poly.verts[segment[1]]])
	if face == 'l':
		p = rect.ll
		n = Vector(-1, 0, -rect.dim.w*scale)
	elif face == 'r':
		p = rect.ur
		n = Vector(1, 0, -rect.dim.w*scale)
	elif face == 't':
		p = rect.ul
		n = Vector(0, -1, -rect.dim.h*scale)
	elif face == 'b':
		p = rect.lr
		n = Vector(0, 1, -rect.dim.h*scale)
	elif face == 'n':
		p = Point(0,0,near)
		n = Vector(0, 0, -1)
	elif face == 'f':
		p = Point(0,0,far)
		n = Vector(0, 0, 1)
	if face != 'f':
		p.z = near
	l = line.to_vec().to_point()
	n = n.to_point()
	
	# (((0,0,near) - p0) * (0,0,-1)) / ((p1-p0) * (0,0,-1))
	# = (-p0.x, -p0.y, near - p0.z) * (0, 0, -1) = p0.z - near / (p0.z - p1.z)
	# 
	d = ((p - line.points[0]) ** n) / (l ** n)
	if tmp_id == 6:
		print(f"poly_id: {tmp_id}")
		print(f"p: {p}, p0: {line.points[0]}, n: {n}, l: {l}")
		print(f"p - line.points[0]: {p - line.points[0]}")
		print(f"l ** n: {l ** n}")
		print(f"(p - line.points[0]) ** n: {(p - line.points[0]) ** n}")
		print(f"((p - line.points[0]) ** n) / (l ** n): {d}")
	if 0 <= d <= 1:
		p2 = line.lerp(d)
		if face=='l':
			print(f'l: {(rect.p1.x)*(p2.z/near)}')
		elif face=='r':
			print(f'r: {(rect.p2.x)*(p2.z/near)}')
		elif face=='t':
			print(f't: {(rect.p1.y)*(p2.z/near)}')
		elif face=='b':
			print(f'l: {(rect.p2.y)*(p2.z/near)}')
		elif face=='n':
			print(f'n: {near}')
		elif face=='f':
			print(f'f: {far}')
		return p2
	return None
	
def frustum_clip(poly, dim, near, far):
	"""
	vars:
	ofs.0 [(32,0) fixed vec]
	v.16 [(1,15) fixed vec, actual value is / 2]
	s = integer vec
	t = integer texcoord (u,v,w)
	
	t.w = ofs.16.z / v.16.z [0 bit frac/integer res] 
	s.x = (ofs.16.x + (v.16.x * t.w)).0
	s.y = (ofs.16.y + (v.16.y * t.w)).0
	
	ofs.16.z = (-32768.0, 32767.0)
	v.16.z = (-0.5, 0.49998)
	
	without adding ofs.x and ofs.y:
	
	t.w = ofs.16.z / v.16.z [0 bit frac/integer res] 
	s.x = (v.16.x * t.w).0
	s.y = (v.16.y * t.w).0
	
	at ofs.16.z == v.16.z, s.x,s.y map directly to centered screen coords
	
	this means that (-ofs.16.x, -ofs.16.y, ofs.16.z) in view coords maps 
	to the upper-left of the screen in screen coords
	
	
	but the frustum is in 
	---------
	
	
	
	
	"""
	
	bitset_count = [0, 1, 1, 2, 1, 2, 2, 3]
	bitset_vert_idx = [-1, 2, 1, 0, 0, 1, 2, -1]
	bitset_inside_idxs = [(-1, -1), (2, -1), (1, -1),  (1,  2), 
						   (0, -1), (0,  2), (0,  1), (-1, -1)]
	bitset_others_idxs = [(-1, -1), (0,  1), (0,  2),  (1,  2), 
						   (1,  2), (0,  2), (0,  1), (-1, -1)]
	
	rect = Rect2d(-dim/2, dim)
	
	for plane in ['n']: #'l', 'r', 't', 'b', 'n', 'f']:
		new_verts = []
		new_polys = []
		inside = []
		for vert in poly.verts:
			if vert.x != vert.x or vert.y != vert.y or vert.z != vert.z:
				return -1
		if plane == 'l':
			for vert in poly.verts:
				inside.append(int(vert.x) >= int((rect.p1.x)*(vert.z/near)))
		elif plane == 'r':
			for vert in poly.verts:
				inside.append(int(vert.x) <= int((rect.p2.x)*(vert.z/near)))
		elif plane == 't':
			for vert in poly.verts:
				inside.append(int(vert.y) >= int((rect.p1.y)*(vert.z/near)))
		elif plane == 'b':
			for vert in poly.verts:
				inside.append(int(vert.y) <= int((rect.p2.y)*(vert.z/near)))
		elif plane == 'n':
			for vert in poly.verts:
				inside.append(int(vert.z) >= int(near))
		elif plane == 'f':
			for vert in poly.verts:
				inside.append(int(vert.z) <= int(far))
		bits = pack_bits(inside)
		count = bitset_count[bits]
		if count == 3: continue
		elif count == 0: return -1
		for ii in range(2):
			idx = bitset_inside_idxs[bits][ii]
			if idx == -1: break
			new_verts.append(poly.verts[idx])
		vidx = bitset_vert_idx[bits]
		for ii in range(2):
			idx = bitset_others_idxs[bits][ii]
			segment = (vidx, idx)
			new_vert = face_intersection(poly, segment, plane, rect, near, far) 
			new_verts.append(new_vert)
		new_polys.append(Poly(new_verts[0:3]))
		if len(new_verts) > 3:
			new_polys.append(Poly(new_verts[1:4]))
		return new_polys
	return 0
	
"""
[([(-709.7222 , -687.8472 , 350.), (-613.7153 , -687.8472 , 350.), (-709.77606, -688.21155, 288.)], [(0., 0., 1.), (0., 0., 1.), (0., 0., 1.)], -1, 0, 0), ([(-613.7153 , -687.8472 , 350.), (-709.77606, -688.21155, 288.), (-671.004  , -688.21155, 288.)], [(0., 0., 1.), (0., 0., 1.), (0., 0., 1.)], -1, 0, 0)]
"""

def clip_polys2(polys, dim, near, far):
	global tmp_id
	clipped = []
	clip_queue = [poly for poly in polys]
	lst = list(polys)
	while len(clip_queue) > 0:
		poly = clip_queue.pop(0)
		if poly in lst:
			tmp_id = lst.index(poly)
		#print(tmp_id)
		res = frustum_clip(poly, dim, near, far)
		if res == 0:
			clipped.append(poly)
		elif res != -1:
			clip_queue.extend(res)
		#print(len(clip_queue))
	print(f"{len(clipped)} polys after clipping")
	return clipped

def unproject_polys(polys, dim, near):
	offset = dim.to_point() / 2
	for poly in polys:
		for vert, vertuvw in zip(poly.verts, poly.vertuvws):
			vert.x = ((vert.x*offset.x) / (vertuvw.w))*65536
			vert.y = ((vert.y*offset.y) / (vertuvw.w))*65536
			vert.z = vert.z
	return polys

"""
if written == False:
		flat = [[poly.verts[0].x, poly.verts[0].y, poly.verts[0].z,
		        poly.verts[1].x, poly.verts[1].y, poly.verts[1].z,
		        poly.verts[2].x, poly.verts[2].y, poly.verts[2].z]
		        for poly in polys]
		df = pd.DataFrame(flat)
		df.to_csv("polys_proj.csv")
		written = True
"""

# -320 * 0.004
def reproject_polys(polys, dim, near):
	offset = dim.to_point() / 2
	for poly in polys:
		for vert, vertuvw in zip(poly.verts, poly.vertuvws):
			vert.x = (vert.x*vertuvw.w) / offset.x
			vert.y = (vert.y*vertuvw.w) / offset.y
			vert.z = vert.z * 65536
	return polys
	
class ContextProcessed3d(VBOContext):
	def __init__(self, nsf, w, h):
		super().__init__(w, h, dimensions=3, indexed=False, colors_enabled=False)
		self.zone_idx = 0
		self.zones = [entry for page in nsf.pages
							if page.type != 1
							for entry in page.entries 
							if entry.type == 7]
		self.zones.sort(key=lambda e: e.eid.value)
		self.scene = Scene(nsf, self.zones[0], w, h)
		self.scene.path_idx = 0
		self.progress = 0
		self.poly_ids_clipped = None
		self.polys_clipped = None
		self.rot = 0
		self.update_state(0) 
		self.do_update = True
		self.camera = GLCamera()
		
		self.scene.all_poly_ids()
		self.scene.project()
		self.scene.compute_visible_polys(self.w, self.h)
			
	def draw(self):
		super().draw()
		if self.do_update:
			
			self.scene.all_poly_ids()
			self.scene.project()
			
			dim = Dimensions(self.w, self.h)
			self.quads, self.lines = build_frustum(dim, 288, 30000)
			self.upload_quads(self.quads)
			self.upload_lines(self.lines)
			#unproject_polys(self.scene.polys, dim, 288)			
			#self.polys_clipped = clip_polys2(self.scene.polys, dim, 288, 30000)
			self.poly_ids_clipped, self.polys_clipped = \
				clip_polys(self.scene.poly_ids, self.scene.polys)
			unproject_polys(self.polys_clipped, dim, 288)
			
			self.polys_clipped = np.array(self.polys_clipped, dtype=Poly)
			#self.upload_polys(self.polys_clipped)
			self.upload_polys(self.polys_clipped)
			self.do_update = False
		
		#gluPerspective(45, self.w/self.h, 0.1, 1000.0)
		glOrtho(-1.0,1.0,-1.0,1.0,288,30000.0)
		glColor3f(1.0, 1.0, 1.0)
		#glTranslatef(0.0,0.0,16384)
		glScalef(1/16384.0,1/16384.0,1/16384.0)
		
		self.camera.update(self.keys)
		#glRotatef(self.rot, 0.0, 1.0, 0.0)
		#self.draw_polys()
		self.draw_lines()
		self.draw_polys_wireframe()
		self.draw_quads_wireframe()
		#self.rot += 0.1
		
		self.flush()
		
	def update(self):
		inc_val = 1
		delta_progress = 0
		if self.keys[b'x']:
			delta_progress = -inc_val
		elif self.keys[b's']:
			delta_progress = inc_val
		if delta_progress:
			self.update_state(delta_progress)
	
	def update_state(self, delta_progress):
		"""
		updates the current (zone, path, path point) given a change in 
		'progress' (number of path points to move forward or back)
		"""
		new_progress = self.scene.path_pt_idx + delta_progress
		
		# scene currently renders only (the worlds of and from path of)
		# one zone at a time. so we have to change that current zone to
		# a neighbor zone when boundary conditions are met
		if self.scene.path_idx == 0 and \
				new_progress < 0 and \
				self.zone_idx > 0:
			self.zone_idx -= 1
			self.scene.zone = self.zones[self.zone_idx]
			self.scene.path_pt_idx = len(self.scene.zone.paths[-1].points)-1
			self.scene.path_idx = len(self.scene.zone.paths)-1
			self.scene.update_poly_ids(self.scene.path_idx, 
				self.scene.path_pt_idx, 'forward')
		elif self.scene.path_idx == len(self.scene.zone.paths)-1 and \
				new_progress >= len(self.scene.zone.paths[-1].points)-1 and \
				self.zone_idx < len(self.zones):
			self.zone_idx += 1
			self.scene.zone = self.zones[self.zone_idx]
			self.scene.path_pt_idx = 0
			self.scene.path_idx = 0
			self.scene.update_poly_ids(self.scene.path_idx, 
				self.scene.path_pt_idx, 'backward')
		else:
			self.scene.update_path(self.scene.path_idx, new_progress)
		
		self.do_update=True
		
"""
poly_id: 6
p: (0., 0., 288.), 
p0: (-709.8125, -688.4584, 246.), 
n: (0., 0., -1.), 
l: (96.09723, 0.611145, 104.)
p - line.points[0]: (709.8125, 688.4584, 42.)
l ** n: -104.0
(p - line.points[0]) ** n: -42.0
((p - line.points[0]) ** n) / (l ** n): 0.4038461446762085
"""

class Context(VBOContext):
	def __init__(self, w, h, dimensions=3):
		super().__init__(w, h, dimensions=dimensions, colors_enabled=False)
		# initialize global primitive buffers here
		# also any non-dynamic primitive buffers should be uploaded here
		# with self.upload_<prim_type>(data)
		self.polys = np.array([Poly([Point(-0.5,-0.5,-0.5), Point(0.5,0.2,-0.5),
		                    Point(0.0,0.0,0.5)])])
		self.bound = Rect3d(Point(-1.0,-1.0,0.0), Dimensions(2.0,2.0,10.0))
		self.quads = np.array([face.to_quad() for face in self.bound.get_faces()])
		for poly in self.polys:
			for vert, vertuvw in zip(poly.verts, poly.vertuvws):
				vertuvw.z = 288 / vert.z
		self.poly_ids = np.array([PolyId()])
		ids, clipped = clip_polys(self.poly_ids, self.polys)
		self.polys_clipped = np.array(clipped, dtype=Poly)
		print(type(self.polys_clipped))
		self.rot = 0
		
	def draw(self):
		self.update()
		gluPerspective(45, self.w/self.h, 0.1, 1000.0)
		# do drawing code here
		# use self.draw_<prim_type>s([data]) passing optional data arg 
		# if prims are dynamic 
		self.rot += 0.001
		glColor3f(1.0,1.0,1.0)
		glRotatef(self.rot, 1.0, 1.0, 0.0)
		self.draw_polys_wireframe(np.concatenate([self.polys, self.polys_clipped]))
		self.draw_quads_wireframe(self.quads)
	
		self.flush()
		
	def update(self):
		# do non-graphical updating logic here
		pass
		
	def keys(self, key, x, y):
		# handle keys here
		pass

def main():
	nsf_path = "../../utils/gen_level/S0000001.NSF"
	nsd_path = nsf_path[:-1] + 'D'
	with open(nsf_path, "rb") as nsf_file:
		nsf_data = nsf_file.read()
	with open(nsd_path, "rb") as nsd_file:
		nsd_data = nsd_file.read()
	nsd = Nsd.from_cbytes(nsd_data)
	nsf = Nsf.from_cbytes(nsf_data, nsd)
	lib.nsd_read(nsd.cbytes)
	lib.nsf_read(nsf.cbytes, nsd.cptr)
	dim = Dimensions(512, 256)
	context = ContextProcessed3d(nsf, dim.w, dim.h)
	context.loop()
	
if __name__ == '__main__':
	main()

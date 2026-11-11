import os
import sys
sys.path.append('/home/user/src/pylibcrash')

sys.path.append('/home/user/src/pylibcrashutils')
from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.vbo_context import VBOContext


from copy import copy
import numpy as np
import random

from OpenGL.GL import *
from OpenGL.GLUT import *

def clamp(v,vmin,vmax):
	return min(max(v,vmin),vmax)
	
def is_actually_a_poly(poly):
	if poly.verts[0].x == poly.verts[1].x \
			and poly.verts[0].y == poly.verts[1].y:
		return False
	if poly.verts[0].x == poly.verts[2].x \
			and poly.verts[0].y == poly.verts[2].y:
		return False
	if poly.verts[1].x == poly.verts[2].x \
			and poly.verts[1].y == poly.verts[2].y:
		return False
	return True
	
def split_cond(lst, cond):
	true_list, false_list = [], []
	for item in lst:
		if cond(item) == True:
			true_list.append(item)
		else:
			false_list.append(item)
	return true_list, false_list
	
def test_poly_with_edge(poly, edge, val):
	tests = {'left': lambda v: v.x > val,
	         'right': lambda v: v.x < val,
	         'top': lambda v: v.y > val,
	         'bottom': lambda v: v.y < val}
	test = tests[edge]
	return split_cond(poly.verts, test)
	
def clip_poly_with_edge(poly, edge, val):
	inside, outside = test_poly_with_edge(poly, edge, val)
	if len(outside) == 0: return [poly]
	elif len(inside) == 0: return []
	if edge in ['top', 'bottom']:
		for vert in poly.verts: vert.x,vert.y = vert.y,vert.x
	v = inside[0] if len(inside) == 1 else outside[0]
	others = outside if len(inside) == 1 else inside
	new_verts = copy(inside)
	for u in others:
		ab = v.y + (val-v.x)*(u.y-v.y)/(u.x-v.x)
		new_vert = Point(ab,val) if edge in ['top', 'bottom'] \
			  else Point(val,ab)
		new_verts.append(new_vert)
	if edge in ['top', 'bottom']:
		for vert in poly.verts: vert.x,vert.y = vert.y,vert.x
	new_polys = [Poly(new_verts[0:3],[1,1,1])]
	if len(new_verts) > 3:
		new_polys.append(Poly(new_verts[1:4],[1,1,1]))
	new_polys = [poly for poly in new_polys if is_actually_a_poly(poly)]
	return new_polys

def clip_poly(poly, l=-1.0, r=1.0, t=-1.0, b=1.0):
	edges = [('left', l), ('right', r), ('top', t), ('bottom', b)]
	clipped = []
	to_clip = [poly]
	while len(to_clip) > 0:
		poly = to_clip.pop(0)
		for edge, val in edges:
			polys = clip_poly_with_edge(poly, edge, val)
			if len(polys) != 1:
				to_clip.extend(polys)
				break
		if len(polys) == 1:
			clipped.append(poly)
	return clipped


bitset_count = [ 0, 1, 1, 2, 1, 2, 2, 3 ]
bitset_vert_idx = [ -1, 2, 1, 0, 0, 1, 2, -1 ]
bitset_inside_idxs = [ [ -1, -1 ], [ 2, -1 ], [ 1, -1 ], [ 1, 2 ], 
					   [  0, -1 ], [ 0,  2 ], [ 0,  1 ], [ -1, -1 ] ]
bitset_others_idxs = [ [ -1, -1 ], [ 0, 1 ], [ 0, 2 ], [ 1, 2 ], 
                       [  1,  2 ], [ 0, 2 ], [ 0, 1 ], [-1,-1 ] ]
edge_values = [ -1.0, 1.0, -1.0, 1.0 ]

def test_poly_alt(poly, edge):
	
	bits = 0
	
	if edge == 0:
		for i in range(3):
			vert = poly.verts[i]
			if vert.x >= edge_values[0]:
				bits |= 1
			bits <<= 1
	if edge == 1:
		for i in range(3):
			vert = poly.verts[i]
			if vert.x <= edge_values[1]:
				bits |= 1
			bits <<= 1
	if edge == 2:
		for i in range(3):
			vert = poly.verts[i]
			if vert.y >= edge_values[2]:
				bits |= 1
			bits <<= 1
	if edge == 3:
		for i in range(3):
			vert = poly.verts[i]
			if vert.y <= edge_values[3]:
				bits |= 1
			bits <<= 1
	bits >>= 1
	return bits
	
def is_valid_poly(poly):
	for i in range(3):
		if poly.verts[i].x == poly.verts[(i+2)%3].x and \
				poly.verts[i].y == poly.verts[(i+2)%3].y:
			return False
		if poly.verts[i].x != poly.verts[i].x or \
			poly.verts[i].y != poly.verts[i].y:
			return False
	return True
  
def swap_poly_xy(poly):
	for vert in poly.verts:
		vert.x, vert.y = vert.y, vert.x
	return poly

def polys_eq(a,b):
	for i in range(3):
		if a.verts[i].x != b.verts[i].x or \
		   a.verts[i].y != b.verts[i].y:
		   return False
	return True
	
def clip_poly_alt(src_poly):
	dst_polys = []
	
	for i in range(4):
		bits = test_poly_alt(src_poly, i)
		count = bitset_count[bits]
		if count==3: continue
		elif count==0: return -1, dst_polys
		if i>=2: swap_poly_xy(src_poly)
		new_verts = []
		new_vertuvws = []
		for ii in range(2):
			idx = bitset_inside_idxs[bits][ii]
			if idx==-1: break
			new_verts.append(src_poly.verts[idx])
			new_vertuvws.append(src_poly.vertuvws[idx])
		val = edge_values[i]
		vert_idx = bitset_vert_idx[bits]
		
		vert = src_poly.verts[vert_idx]
		vertuvw = src_poly.vertuvws[vert_idx]
		for ii in range(2):
			idx = bitset_others_idxs[bits][ii]
			print(f"idx: {idx}")
			other = src_poly.verts[idx]
			otheruvw = src_poly.vertuvws[idx]
			t = (val-vert.x)/(other.x-vert.x)
			xy = vert.y + t*(other.y-vert.y);
			z = vert.z + t*(other.z-vert.z);
			w = vertuvw.w + t*(otheruvw.w-vertuvw.w);
			print(f"val: {val}, vert.x: {vert.x}, other.x: {other.x}")
			print(f"{t}, {xy}, {z}, {w}")
			new_vert = Point(0,0,0)
			new_vert.x = xy if i>=2 else val
			new_vert.y = val if i>=2 else xy
			new_vert.z = z
			new_vertuvw = Texcoord(0,0,w)
			new_verts.append(new_vert)
			new_vertuvws.append(new_vertuvw)	
		if i >= 2: swap_poly_xy(src_poly)
		new_poly = Poly(new_verts[0:3], new_vertuvws[0:3])
		if is_valid_poly(new_poly):
			print(f"new poly at idx {len(dst_polys)}")
			print(new_poly)
			dst_polys.append(new_poly)
		if len(new_verts) > 3:
			new_poly = Poly(new_verts[1:4], new_vertuvws[1:4])
			if is_valid_poly(new_poly):
				print(f"new poly at idx {len(dst_polys)}")
				print(new_poly)
				dst_polys.append(new_poly)
		if len(dst_polys) == 0: return -1, dst_polys
		#if len(dst_polys) == 1:
		#	if polys_eq(dst_polys[0], src_poly):
		#		return 0, []
		return 1, dst_polys
	return 0, dst_polys

def clip_polys_alt(dst_ids, dst_polys, src_ids, src_polys):
	idx_stack = []
	for i in range(len(src_polys)-1,-1,-1):
		idx_stack.append(i)
  
	while len(idx_stack) > 0:
		#print(f"idx_stack: {idx_stack}")
		#print("popping idx stack")
		idx = idx_stack.pop()
		print(f"idx: {idx}")
		if idx < 0:
			poly = dst_polys[-idx-1]
			poly_id = dst_ids[-idx-1]
		else:
			poly = src_polys[idx]
			poly_id = src_ids[idx]

		#print(f"poly: {poly}, poly_id: {poly_id}")
		res, clipped = clip_poly_alt(poly)
		print(f"res: {res}, count:{len(clipped)}")
		#print(f"clip result: {res}, {clipped}")
		
		if res == 1:  # poly was clipped
			#print("poly clipped. appending idxes of results to idx stack")
			if idx < 0:
				idx = -idx-1
			else:
				#print("poly clipped was a pure src poly. not yet in result, " 
				#    + "so appending the l clipped poly")
				idx = len(dst_polys)
				dst_polys.append(None)
				dst_ids.append(None)
			dst_polys[idx] = clipped[0]
			dst_ids[idx] = poly_id
			idx_stack.append(-idx-1)
			if len(clipped) == 2:
				#print("also there is a r clipped poly so appending that")
				idx = len(dst_polys)
				dst_polys.append(clipped[1])
				dst_ids.append(poly_id)
				idx_stack.append(-idx-1)
		elif res == 0:
			#print("poly entirely within screen bounds. no clip, just append")
			dst_polys.append(poly)
			dst_ids.append(poly_id)
		#print(f"dst_polys: {dst_polys}")
		#print(f"dst_ids: {dst_ids}")

class Context(VBOContext):
	def __init__(self, w, h):
		super().__init__(w, h, 2, colors_enabled=False)
		self.poly = Poly([Point(0,-0.5,0),
						  Point(-0.5,0.5,0), 
						  Point(0.5,0.5,0)], [1,1,1])
		self.vert_idx = 0
		
	def draw(self):
		glColor3f(1.0,1.0,1.0)
		ids = []
		polys = []
		#print("drawing")
		for i in range(10):
			verts = []
			for ii in range(3):
				x = random.randint(0,100)/25 - 2.0
				y = random.randint(0,100)/25 - 2.0
				#z = random.randint(0,100)/25 - 2.0
				#w = ...
				vert = Point(x,y) #,z)
				verts.append(vert)
			poly = Poly(verts, [1,1,1])
			polys.append(poly)
			ids.append(i)
		#polys = [self.poly]
		#ids = [0]

		new_ids = []
		new_polys = []
		clip_polys_alt(new_ids, new_polys, ids, polys)
		polys = new_polys
		
		#polys = clip_poly(self.poly)
		polys = np.array(polys)
		
		self.draw_polys_wireframe(polys)
		self.print(-0.8,-0.8,f"current vert:{self.vert_idx}")
		self.flush()
		
	def keys(self, key, x, y):
		vert = self.poly.verts[self.vert_idx]
		if key == b'q':
			self.vert_idx = clamp(self.vert_idx-1,0,2)
		elif key == b'e':
			self.vert_idx = clamp(self.vert_idx+1,0,2)
		elif key == b'w':
			vert.y = clamp(vert.y-0.01,-2.0,2.0)
		elif key == b'a':
			vert.x = clamp(vert.x-0.01,-2.0,2.0)
		elif key == b's':
			vert.y = clamp(vert.y+0.01,-2.0,2.0)
		elif key == b'd':
			vert.x = clamp(vert.x+0.01,-2.0,2.0)

def main():
	context = Context(640,480)
	context.loop()
	
if __name__ == '__main__':
	main()

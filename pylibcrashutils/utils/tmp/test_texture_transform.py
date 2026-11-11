import os
import sys
sys.path.append('/home/user/src/pylibcrash')
import random

import numpy as np

import PIL
from PIL import Image

from gfx.general.geom import *
from gfx.texture import *

import pygame

def image_to_texture(image, name):
	dim = Dimensions(image.width, image.height)
	data = np.frombuffer(image.tobytes(), dtype=np.uint32)
	data = data.reshape((int(dim.w), int(dim.h)))
	tex = Texture(name, dim, data) 
	return tex

def texture_region_to_rect(texture, poly, dim):
	"""
	transforms a polygonal region of a texture to an upper-left right
	triangle
	"""
	v0,v1,v2 = poly.verts[0], poly.verts[1], poly.verts[2]
	v10, v21, v02 = v1 - v0, v2 - v1, v0 - v2
	
	mn = Point(int(min(min(v0.x,v1.x),v2.x)), int(min(min(v0.y,v1.y),v2.y)))
	mx = Point(int(max(max(v0.x,v1.x),v2.x)), int(max(max(v0.y,v1.y),v2.y)))
	mm = Point(mn.x,mx.y)
	det = Point((v0*v1).z,(v1*v2).z,(v2*v0).z)
	gabd = Point((v10*v2).z, (v21*v0).z, (v02*v1).z) + det
	gab = (Point((v10*mm).z, (v21*mm).z, (v02*mm).z) + det) / gabd
	abgd = Point(gabd.y, gabd.z, gabd.x)
	dy = Point(v10.y, v21.y, v02.y) / abgd
	dx = (Point(v10.x, v21.x, v02.x) / abgd) - (dy*(mx.x-mn.x))
	
	res = np.ndarray((int(dim.w),int(dim.h)), dtype=np.uint32)
	res[:] = 0
	for y in range(int(mx.y),int(mn.y),-1):
		for x in range(int(mn.x),int(mx.x)):
			if gab.x >= 0 and gab.y >= 0 and gab.z >= 0:
				di = (int(gab.y*dim.w), int(gab.z*dim.h))
				si = (x % int(texture.dim.w), y % int(texture.dim.h)) 
				if di[0] >= dim.w or di[1] >= dim.h:
					continue
				res[di] = texture.data[si]
			gab -= dy
		gab -= dx
	#return res
	
def texture_region_to_rect2(texture, poly, dim):
	v0, v1, v2 = tuple(poly.verts)
	
	v10 = v1 - v0
	v20 = v2 - v0
	
	dx = v10 / int(dim.w)
	dy = v20 / int(dim.h)
	cur_y, cur = Point(v0.x, v0.y), Point(v0.x, v0.y)
	
	res = np.ndarray((int(dim.h),int(dim.w)),dtype=np.uint32)
	res[:] = 0
	for y in range(int(dim.h)):
		cur = Point(cur_y.x, cur_y.y)
		for x in range(int(dim.w)):
			si = (int(cur.y), int(cur.x))
			si = (si[0] % int(texture.dim.h), si[1] % int(texture.dim.w))
			di = (y,x)
			res[di] = texture.data[si] 
			cur += dx
		cur_y += dy
	return res
	

def texture_quad_to_rect(texture, poly, dim):
	v3 = poly.verts[2] + (poly.verts[0] - poly.verts[1])
	poly_a = poly
	poly_b = Poly([v3,poly.verts[2],poly.verts[0]], [0,0,0])
	
	r1 = texture_region_to_rect(texture, poly_a, dim)
	r2 = texture_region_to_rect(texture, poly_b, dim)
	for y in range(int(dim.h)):
		for x in range(int(dim.w)-y):
			r1[(int(dim.w)-1-x,int(dim.h)-1-y)]=r2[(x,y)]
	return r1
	
dim = Dimensions(640,480)
src_dir = "/home/user/src/genlevel/castle_exterior"
names = os.listdir(src_dir)
names = [name for name in names if name.endswith(".png")]
paths = [src_dir + '/' + name for name in names]
images = [Image.open(path) for path in paths]
image = images[0]
image = image.convert("RGBA")
image = image.resize((image.width*4, image.height*4))
tex = image_to_texture(image, names[0])

pygame.init()
screen = pygame.display.set_mode([dim.w,dim.y])
img = pygame.image.frombuffer(image.tobytes(), (image.width,image.height), 'RGBA')
bimg = img

verts = [Point(0.5,0.25),Point(0.25,0.75),Point(0.75,0.75)]
vert_selected = None

done = False
keys = {}
mouse_down = False
mouse_down_prev = False
mouse_pos = None
while not done:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done=True
		if event.type == pygame.KEYDOWN:
			keys[event.key] = 1
		if event.type == pygame.KEYUP:
			keys[event.key] = 0
		if event.type == pygame.MOUSEBUTTONDOWN:
			mouse_down = True
		if event.type == pygame.MOUSEBUTTONUP:
			mouse_down = False
		if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, 
						  pygame.MOUSEMOTION]:
			mouse_pos = event.pos
	
	if mouse_down and not mouse_down_prev:
		print("clicked")
		pos = Point(mouse_pos[0], mouse_pos[1])
		for idx, vert in enumerate(verts):
			v = vert.vmul(dim)
			dist = Vector.from_point(pos - v).magnitude()
			print(dist)
			if dist < 20:
				vert_selected = idx
	if not mouse_down and mouse_down_prev:
		vert_selected = None
		
	if vert_selected is not None:
		idx = vert_selected
		verts[idx].x = mouse_pos[0] / dim.w
		verts[idx].y = mouse_pos[1] / dim.h
	
	tv = [vert.vmul(dim) for vert in verts]
	
	screen.fill((0,0,0))
	for idx in range(3):
		pygame.draw.line(screen, (255,255,255), \
		                 (tv[idx].x,tv[idx].y), \
		                 (tv[(idx+1)%3].x, tv[(idx+1)%3].y))
	
	if keys.get(pygame.K_a):
		poly = Poly(tv, [0,0,0])
		buf = texture_region_to_rect2(tex, poly, Dimensions(128,128))
		bimg = pygame.image.frombuffer(buf.tobytes(), buf.shape, 'RGBA')
		
	screen.blit(img, (0,0))
	screen.blit(bimg, (320,240))
	pygame.display.flip()
	
	mouse_down_prev = mouse_down
	

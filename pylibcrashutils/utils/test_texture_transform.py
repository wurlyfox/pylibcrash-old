import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')
import random

import numpy as np

import PIL
from PIL import Image

from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.general.texture import *

import pygame
import pygame.gfxdraw
from OpenGL.GL import *
from OpenGL.GLU import *

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

gl_texture_map = {}
def using_texture(image, texid, fn):
	if texid not in gl_texture_map:
		gl_texture_map[texid] = glGenTextures(1)
	glActiveTexture(GL_TEXTURE0);
	glBindTexture(GL_TEXTURE_2D, gl_texture_map[texid])
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0,
		GL_RGBA, GL_UNSIGNED_BYTE, image.tobytes())
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
	glEnable(GL_TEXTURE_2D)
	fn()
	glDisable(GL_TEXTURE_2D)
	glBindTexture(GL_TEXTURE_2D, 0)

def gl_draw_image(image, loc, dim_screen, texid, scale=1):
	
	loc = Point(loc[0], loc[1])
	dim = Dimensions(image.width*scale, image.height*scale)
	
	loc = Point(((loc.x / dim_screen.w) * 2) - 1,
	            ((loc.y / dim_screen.h) * 2) - 1)
	dim = Dimensions(((dim.w / dim_screen.w) * 2),
	                 ((dim.h / dim_screen.h) * 2))
	
	rect = Rect2d(loc, dim) 
	quad = rect.to_quad()
	uvs = Rect2d(Point(0,0),Dimensions(1,1)).to_quad()
	
	def draw_quad():
		glBegin(GL_QUADS)
		for vert, uv in zip(quad.verts, uvs.verts):
			glTexCoord2f(uv.x, uv.y)
			glVertex2f(vert.x, -vert.y)
		glEnd()
	using_texture(image, texid, draw_quad)
	
def gl_draw_textured_poly(image, poly, texid):
	
	# poly is already normalized
	uvs = [Point(0.0, 0.0), Point(1.0, 0.0), Point(0.0, 1.0)]
	
	def draw_poly():
		glBegin(GL_TRIANGLES)
		for vert, uv in zip(poly.verts, uvs):
			glTexCoord2f(uv.x, uv.y)
			glVertex2f(vert.x, -vert.y)
		glEnd()
	using_texture(image, texid, draw_poly)
	
def gl_draw_pygame_surface(surface, dim_screen):
	texid = 0
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	glClearColor(0, 0, 0, 1.0)
	data = pygame.image.tostring(surface, 'RGBA')
	image = Image.frombuffer('RGBA', surface.get_size(), data)
	gl_draw_image(image, (0,0), dim_screen, texid)
	glDisable(GL_BLEND)

class PygameContext:
	
	def __init__(self, dim, use_gl):
		self.dim = dim
		self.use_gl = use_gl
		self.screen = self.init_pygame(dim, use_gl)
		self.done = False
		self.keys = {}
		self.mouse_down = False
		self.mouse_down_prev = False
		self.mouse_pos = None
	
	@staticmethod
	def init_pygame(dim, use_gl):
		res = [dim.w, dim.h]
		flags = 0
		if use_gl == True:
			flags = pygame.DOUBLEBUF | pygame.OPENGLBLIT
			gluPerspective(45, dim.w/dim.h, 0.1, 100.0)
		screen = pygame.display.set_mode(res, flags)
		return screen
		
	def loop(self):
		mouse_events = [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, 
						pygame.MOUSEMOTION]
		while not self.done:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.done=True
				if event.type == pygame.KEYDOWN:
					self.keys[event.key] = 1
				if event.type == pygame.KEYUP:
					self.keys[event.key] = 0
				if event.type == pygame.MOUSEBUTTONDOWN:
					self.mouse_down = True
				if event.type == pygame.MOUSEBUTTONUP:
					self.mouse_down = False
				if event.type in mouse_events:
					self.mouse_pos = event.pos
				if self.mouse_down and not self.mouse_down_prev:
					self.on_click(self.mouse_pos)
				if not self.mouse_down and self.mouse_down_prev:
					self.on_unclick(self.mouse_pos)
			self.update()
			self.mouse_down_prev = self.mouse_down
			pygame.display.flip()
		
	def update(self):
		pass
		
	def on_click(self, pos):
		pass
		
	def on_unclick(self, pos):
		pass

def get_image():
	idx = 8
	src_dir = "/home/user/src/genlevel/castle_exterior"
	names = os.listdir(src_dir)
	names = [name for name in names if name.endswith(".png")]
	paths = [src_dir + '/' + name for name in names]
	images = [Image.open(path) for path in paths]
	image = images[idx]
	image = image.convert("RGBA")
	image = image.resize((image.width*2, image.height*2))
	return image, names[idx]
		
class Context(PygameContext):
	def __init__(self, dim, use_gl):
		super().__init__(dim, use_gl)
		self.init_images()
		self.verts = [Point(0.0,-0.5),Point(-0.5,0.5),Point(0.5,0.5)]
		self.vert_selected = None
		
	def init_images(self):
		image, name = get_image()
		self.texture = image_to_texture(image, name)
		if self.use_gl:
			self.image = image
			self.bimage = image
			self.surface = pygame.Surface((self.dim.w, self.dim.h), pygame.SRCALPHA)
			self.image_pg = pygame.image.frombuffer(image.tobytes(), 
				(image.width, image.height), 'RGBA')
		else:
			self.image = pygame.image.frombuffer(image.tobytes(), 
				(image.width, image.height), 'RGBA')
			self.bimage = self.image
				
	def on_click(self, pos):
		print("clicked")
		pos = Point(pos[0], pos[1])
		for idx, vert in enumerate(self.verts):
			v = vert.denormalize(self.dim)
			dist = Vector.from_point(pos - v).magnitude()
			if dist < 20:
				self.vert_selected = idx
				
	def on_unclick(self, pos):
		self.vert_selected = None
		
	def update(self):
		self.screen.fill((0,0,0))
		if self.use_gl:
			glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
			
		# allow the user to move a vertex currently selected with the mouse
		if self.vert_selected is not None:
			idx = self.vert_selected
			pos = Point(self.mouse_pos[0], self.mouse_pos[1])
			pos = pos.normalize(self.dim)
			self.verts[idx].x = pos.x
			self.verts[idx].y = pos.y
			
		tv = [vert.denormalize(self.dim) for vert in self.verts]
		if self.use_gl == False:
			for idx in range(3):
				pygame.draw.line(screen, (255,255,255), \
								 (tv[idx].x,tv[idx].y), \
								 (tv[(idx+1)%3].x, tv[(idx+1)%3].y))
		else:
			glBegin(GL_LINE_LOOP)
			glColor3f(1.0, 1.0, 1.0)
			for idx in range(3):
				glVertex2f(self.verts[idx].x, -self.verts[idx].y)
			glEnd()
	
		if self.keys.get(pygame.K_a):
			poly = Poly(tv)
			buf = texture_region_to_rect2(self.texture, poly, Dimensions(128,128))
			if self.use_gl == False:
				self.bimage = pygame.image.frombuffer(buf.tobytes(), 
					buf.shape, 'RGBA')
			else:
				self.bimage = Image.frombuffer('RGBA', buf.shape, 
					buf.tobytes())
	
		if self.use_gl == False:
			coords = [(v.x+150, v.y+150) for v in tv]
			pygame.gfxdraw.textured_polygon(self.screen, coords, bimg, 0, 0)
			self.screen.blit(self.image, (0,0))
			#self.screen.blit(self.bimage, (320,240))
		else:
			coords = [Point(vert.x+0.5, vert.y-0.5) for vert in self.verts]
			poly = Poly(coords)
			gl_draw_textured_poly(self.bimage, poly, 3)
			gl_draw_image(self.image, (0,0), self.dim, 1, 2)
			#gl_draw_image(self.bimage, (320,240), self.dim, 2, 2)
			self.surface.fill((0,0,0,0))
			coords = [(v.x+150, v.y+150) for v in tv]
			pygame.gfxdraw.textured_polygon(self.surface, coords, 
											self.image_pg, 0, 0)
			gl_draw_pygame_surface(self.surface, self.dim)

def main():
	dim = Dimensions(640, 480)
	use_gl = True
	context = Context(dim, use_gl)
	context.loop()
	
if __name__ == '__main__':
	main()

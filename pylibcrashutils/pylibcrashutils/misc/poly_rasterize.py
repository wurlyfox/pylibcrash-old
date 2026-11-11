import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')
from pylibcrashutils.gfx.general.geom import *

import pygame
import math
import itertools

class PygameContext:
	def __init__(self, dim):
		self.dim = dim
		self.screen = self.init_pygame(dim)
		self.done = False
		self.keys = {}
		self.mouse_down = False
		self.mouse_down_prev = False
		self.mouse_pos = None
	
	@staticmethod
	def init_pygame(dim):
		pygame.init()
		res = [dim.w, dim.h]
		flags = 0
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

class Context(PygameContext):
	def __init__(self, dim):
		super().__init__(dim)
		self.poly = Poly([Point(2,2,2), Point(4,10,12), Point(12,4,24)])
		
	def draw_poly(self, poly, brightness=None):
		color = tuple([brightness or 255]*3)
		for idx in range(3):
			p1 = (poly.verts[idx].x, poly.verts[idx].y)
			p2 = (poly.verts[(idx+1)%3].x, poly.verts[(idx+1)%3].y)
			pygame.draw.line(self.screen, color, p1, p2)
	
	def draw_rect(self, rect, brightness=None, fill=True):
		color = tuple([brightness or 255]*3)
		rect = (rect.loc.x, rect.loc.y, rect.dim.w, rect.dim.h)
		width = 0 if fill==True else 1
		pygame.draw.rect(self.screen, color, rect, width)
		
	def draw_quad(self, quad, brightness=None):
		color = tuple([brightness or 255]*3)
		for idx in range(4):
			p1 = (quad.verts[idx].x, quad.verts[idx].y)
			p2 = (quad.verts[(idx+1)%4].x, quad.verts[(idx+1)%4].y)
			pygame.draw.line(self.screen, color, p1, p2)
		
	def draw_text(self, text, loc, font=None):
		font = font or pygame.font.Font('freesansbold.ttf', 16)
		text = font.render(text, True, (255,255,255))
		textRect = text.get_rect()
		textRect.center = loc
		self.screen.blit(text, textRect)
		
	def rasterize_poly(self, poly, scale):
		def interpolate(v1, v2):
			dx = (v2.x - v1.x) / (v2.y - v1.y)
			dz = (v2.z - v1.z) / (v2.y - v1.y)
			x = v1.x
			z = v1.z
			for y in range(int(v1.y), int(v2.y)):
				yield int(round(x)),int(round(y)),int(round(z))
				x += dx
				z += dz
		verts = sorted(poly.verts, key=lambda v: v.y)
		v0, v1, v2 = tuple(verts)
		height = v2.y - v0.y
		winding = (((v1.y - v0.y) / height) * (v2.x - v0.x)) + (v0.x - v1.x)
		if winding == 0:
			return
		left = itertools.chain.from_iterable([interpolate(v0, v1), interpolate(v1, v2)])
		right = itertools.chain.from_iterable([interpolate(v0, v2)])
		if winding < 0:
			left, right = right, left
		while True:
			xmin,y,zmin = next(left,(None,None,None))
			xmax,y,zmax = next(right,(None,None,None))
			if y is None:
				break
			if xmin == xmax:
				continue
			dz = (zmax - zmin)/(xmax - xmin)
			z = zmin
			for x in range(xmin, xmax):
				loc = Point(x,y)*scale
				dim = Dimensions(scale, scale)
				#quad = Rect2d(loc, dim).to_quad()
				#self.draw_quad(quad, int(z))
				rect = Rect2d(loc, dim)
				self.draw_rect(rect, int(z))
				z += dz
			
	def update(self):
		def scale_poly(poly, amt):
			return Poly([v*amt for v in poly.verts])
		self.screen.fill((0,0,0))
		poly = scale_poly(self.poly, 5)
		self.rasterize_poly(poly, 5)
		self.draw_poly(scale_poly(poly,5))
	
def main():
	dim = Dimensions(640, 480)
	context = Context(dim)
	context.loop()
	
if __name__ == '__main__':
	main()

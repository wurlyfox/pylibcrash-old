import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')
from pylibcrashutils.gfx.general.geom import *

import pygame

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
		
	def draw_poly(self, poly):
		for idx in range(3):
			p1 = (poly.verts[idx].x, poly.verts[idx].y)
			p2 = (poly.verts[(idx+1)%3].x, poly.verts[(idx+1)%3].y)
			pygame.draw.line(self.screen, (255,255,255), p1, p2)
	
	def draw_quad(self, quad)
		for idx in range(4):
			p1 = (quad.verts[idx].x, quad.verts[idx].y)
			p2 = (quad.verts[(idx+1)%3].x, quad.verts[(idx+1)%3].y)
			pygame.draw.line(self.screen, (255,255,255), p1, p2)
		
	def draw_text(self, text, loc, font=None):
		font = font or pygame.font.Font('freesansbold.ttf', 16)
		text = font.render(text, True, (255,255,255))
		textRect = text.get_rect()
		textRect.center = loc
		self.screen.blit(text, textRect)
		
	def update(self):
		self.screen.fill((0,0,0))
			
def main():
	dim = Dimensions(640, 480)
	context = Context(dim)
	context.loop()
	
if __name__ == '__main__':
	main()

import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')
from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.general.geom_comp import get_poly_winding, get_poly_winding2, get_poly_winding3

import pygame


def get_winding(poly):
	x_order = sorted([0,1,2], key=lambda idx: poly.verts[idx].x)
	y_order = sorted([0,1,2], key=lambda idx: poly.verts[idx].y)
	
	if poly.verts[x_order[0]].x == poly.verts[x_order[1]].x:
		if poly.verts[x_order[2]].x == poly.verts[x_order[1]].x:
			x_order = [tuple(x_order)]
		else:
			x_order = [(x_order[0], x_order[1]), x_order[2]]
	elif poly.verts[x_order[1]].x == poly.verts[x_order[2]].x:
		x_order = [x_order[0], (x_order[1], x_order[2])]
	
	if poly.verts[y_order[0]].y == poly.verts[y_order[1]].y:
		if poly.verts[y_order[2]].y == poly.verts[y_order[1]].y:
			y_order = [tuple(y_order)]
		else:
			y_order = [(y_order[0], y_order[1]), y_order[2]]
	elif poly.verts[y_order[1]].y == poly.verts[y_order[2]].y:
		y_order = [y_order[0], (y_order[1], y_order[2])]
	
	xmins = [x_order[0]] if not isinstance(x_order[0], tuple) else list(x_order[0])
	xmaxs = [x_order[-1]] if not isinstance(x_order[-1], tuple) else list(x_order[-1])
	ymins = [y_order[0]] if not isinstance(y_order[0], tuple) else list(y_order[0])
	ymaxs = [y_order[-1]] if not isinstance(y_order[-1], tuple) else list(y_order[-1])
	
	xmid = x_order[1] if len(x_order) > 2 else None
	ymid = y_order[1] if len(y_order) > 2 else None
	
	def corner_info(pt):
		if pt == xmid and pt == ymid:
			return "UNK"
		vline = pt in xmins and pt in xmaxs
		hline = pt in ymins and pt in ymaxs
		if vline and hline:
			return "POINT"
		elif vline:
			return "VLINE"
		elif hline:
			return "HLINE"
		elif pt in xmins:
			if pt in ymins:
				return "UL"
			elif pt in ymaxs:
				return "LL"
			else:
				return "LEFT"
		elif pt in xmaxs:
			if pt in ymins:
				return "UR"
			elif pt in ymaxs:
				return "LR"
			else:
				return "RIGHT"
		elif pt == xmid:
			if pt in ymins:
				return "UPPER"
			else:
				return "LOWER"
		else:
			return "UNK"
		
	res = []	
	for pt in range(3):
		res.append(corner_info(pt))
	return '\n'.join(res)


# case 1: one angle is 90, rot is 45+(90*n) to 45+(90*(n+1)) range



def poly_rots(poly, retrans=True):
	def rot_point(vert, ang):
		x = (vert.x*math.cos(ang)-vert.y*math.sin(ang))
		y = (vert.x*math.sin(ang)+vert.y*math.cos(ang))
		return Point(x,y)
	def ang(v1, v2):
		#	v1 = Vector.from_point(v1)
		#	v2 = Vector.from_point(v2)
		#	return math.acos((v1 ** v2) / (v1.magnitude()*v2.magnitude()))
		return math.atan2(v2.y, v2.x) - math.atan2(v1.y, v1.x)
	
	v0, v1, v2 = poly.verts
	
	vecs = [v1-v0, v2-v0, v0-v1, v2-v1, v0-v2, v1-v2]
	pts = [v0]*4+[v1]*4+[v2]*4
	angs = [[ang(v,Vector(1,0,0)), ang(v,Vector(0,-1,0))] for v in vecs]
	
	
	polys = []
	for ang, v in zip(list(np.array(angs).ravel()), pts):
		verts = [rot_point(v-vert, ang) for vert in poly.verts]
		if retrans:
			verts = [vert + v for vert in verts]
		polys.append(Poly(verts))	
	return polys
	
def get_nearest(poly):
	
	rots = poly_rots(poly)
	
	dists = [sum([(poly.verts[i].x-rot.verts[i].x)**2
	             +(poly.verts[i].y-rot.verts[i].y)**2
	            for i in range(3)]) for rot in rots]
	nearest = rots[np.argmin(dists)]
	return nearest

def get_winding2(poly):
	
	rots = poly_rots(poly)
	
	dists = [sum([(poly.verts[i].x-rot.verts[i].x)**2
	             +(poly.verts[i].y-rot.verts[i].y)**2
	            for i in range(3)]) for rot in rots]
	nearest = rots[np.argmin(dists)]
	
	# find verts on the same axis
	pairs = [(0,1), (0,2), (1,2)]
	
	same_x = None
	same_y = None
	for pair in pairs:
		if nearest.verts[pair[0]].x == nearest.verts[pair[1]].x:
			same_x = pair
		if nearest.verts[pair[0]].y == nearest.verts[pair[1]].y:
			same_y = pair
	
	# if 2 points with same x then we have an UL, LL or UR, LR
	infos=['','','']
	if same_x is not None:
		other = 3-(same_x[0]+same_x[1])
		verts = nearest.verts
		ul = 'U' if verts[same_x[0]].y < verts[same_x[1]].y else 'L'
		lr = 'L' if verts[same_x[0]].x < verts[other].x else 'R'
		
		infos[same_x[0]] = ul+lr
		ul = 'L' if ul == 'U' else 'U'
		infos[same_x[1]] = ul+lr
		
		mid = (verts[same_x[0]].y + verts[same_x[1]].y)/2
		lr = 'L' if lr == 'R' else 'R'
		ul = 'U' if verts[other].y < mid else 'L'
		infos[other] = ul+lr
	elif same_y is not None:
		other = 3-(same_y[0]+same_y[1])
		verts = nearest.verts
		lr = 'L' if verts[same_y[0]].x < verts[same_y[1]].x else 'R'
		ul = 'U' if verts[same_y[0]].y < verts[other].y else 'L'
		
		infos[same_y[0]] = ul+lr
		lr = 'L' if lr == 'R' else 'R'
		infos[same_y[1]] = ul+lr
		
		mid = (verts[same_y[0]].x + verts[same_y[1]].x)/2
		lr = 'L' if verts[other].x < mid else 'R'
		ul = 'L' if ul == 'U' else 'U'
		infos[other] = ul+lr
	return infos, nearest	            
			
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
		self.verts = [Point(0.0,-0.5),Point(-0.5,0.5),Point(0.5,0.5)]
		self.vert_selected = None
		self.font = pygame.font.Font('freesansbold.ttf', 16)
	
	def on_click(self, pos):
		pos = Point(pos[0], pos[1])
		for idx, vert in enumerate(self.verts):
			v = vert.denormalize(self.dim)
			dist = Vector.from_point(pos - v).magnitude()
			if dist < 20:
				self.vert_selected = idx
				
	def on_unclick(self, pos):
		self.vert_selected = None
		
	def draw_triangle(self, tv, trans=Point(0,0), scale=1):
		for idx in range(3):
			pygame.draw.line(self.screen, (255,255,255), \
							 ((tv[idx].x*scale)+trans.x, \
							  (tv[idx].y*scale)+trans.y), \
							 ((tv[(idx+1)%3].x*scale)+trans.x, \
							  (tv[(idx+1)%3].y*scale)+trans.y))
	
	def draw_text(self, text, loc):
		text = self.font.render(text, True, (255,255,255))
		textRect = text.get_rect()
		textRect.center = loc
		self.screen.blit(text, textRect)
		
	def update(self):
		self.screen.fill((0,0,0))
			
		# allow the user to move a vertex currently selected with the mouse
		if self.vert_selected is not None:
			idx = self.vert_selected
			pos = Point(self.mouse_pos[0], self.mouse_pos[1])
			pos = pos.normalize(self.dim)
			self.verts[idx].x = pos.x
			self.verts[idx].y = pos.y
			
		tv = [vert.denormalize(self.dim) for vert in self.verts]
		poly = Poly(tv)
		#winding = get_winding(poly)
		nearest = get_nearest(poly)
		winding = get_poly_winding2(poly, 'idxes')
		winding = str(winding) #'  '.join(winding)
		self.draw_text(winding, (100,100))
		winding2 = get_poly_winding(poly, 'idxes')
		winding2 = str(winding2)
		self.draw_text(winding2, (100,130))
		winding3 = get_poly_winding3(poly, 'idxes')
		winding3 = str(winding3)
		self.draw_text(winding3, (100,160))
		
		self.draw_triangle(poly.verts, Point(0,0))
		self.draw_triangle(nearest.verts, Point(0,0))

		def avg(lst):
			return sum(lst)/len(lst)
		center = Point(avg([vert.x for vert in poly.verts]), 
					   avg([vert.y for vert in poly.verts]))
		for idx in range(3):
			pygame.draw.line(self.screen, (255,255,255),
							 (tv[idx].x, tv[idx].y),
							 (center.x, center.y))
		
		
def main():
	dim = Dimensions(640, 480)
	context = Context(dim)
	context.loop()
	

	
if __name__ == '__main__':
	main()

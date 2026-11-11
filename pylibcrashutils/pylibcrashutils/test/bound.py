import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')

from pylibcrashutils.gfx.vbo_context import VBOContext
from pylibcrashutils.gfx.general.geom import *

from OpenGL.GL import *
from OpenGL.GLU import *

def build_frustum(dim, near, far):
	
	rect = Rect2d(-dim/2, dim)
	fdim = dim*(far-near)
	frect = Rect2d(-fdim/2, fdim)
	
	nul,nur,nll,nlr = [c+Point(0,0,near) for c in [rect.ul,rect.ur,rect.ll,rect.lr]]
	ful,fur,fll,flr = [c+Point(0,0,far) for c in [frect.ul,frect.ur,frect.ll,frect.lr]]
	
	lquad = Quad([nul, ful, fll, nll])
	rquad = Quad([nur, fur, flr, nlr])
	tquad = Quad([nul, ful, fur, nur])
	bquad = Quad([nll, fll, flr, nlr])
	nquad = Quad([nul, nur, nlr, nll])
	fquad = Quad([ful, fur, flr, fll])
	
	quads = [lquad,rquad,tquad,bquad,nquad,fquad]
	z1 = -(rect.dim.w*(far-near-1))/(2*far-near)
	z2 = -(rect.dim.h*(far-near-1))/(2*far-near)
	normals = [Vector(-1, 0, z1), 
			   Vector(1, 0, z1),
			   Vector(0, -1, z2),
			   Vector(0, 1, z2),
			   Vector(0,0,-rect.dim.w/rect.dim.h), 
			   Vector(0,0,rect.dim.w/rect.dim.h)]
	
	lines = [Line.from_vec(normal, sum(quad.verts, Point(0,0,0))/4)
	         for normal, quad in zip(normals, quads)]
	         
	quads = np.array(quads, dtype=Quad)
	lines = np.array(lines, dtype=Line)
	return quads, lines
	
class Context(VBOContext):
	def __init__(self, w, h, dimensions=3):
		super().__init__(w, h, dimensions=dimensions, colors_enabled=False)
		# initialize global primitive buffers here
		# also any non-dynamic primitive buffers should be uploaded here
		# with self.upload_<prim_type>(data)
		self.quads, self.lines = build_frustum(Dimensions(0.75,0.75), 0.1, 0.4)
		self.upload_lines(self.lines)
		self.upload_quads(self.quads)
		self.rot = 0
		
	def draw(self):
		self.update()
		
		#gluPerspective(45, self.w/self.h, 0.1, 100.0)
		glOrtho(-1.0,1.0,-1.0,1.0,-0.1,2)
		glTranslatef(0.0,0.0,-1.0)
		glRotatef(self.rot,1.0,0.0,0.0)
		
		# do drawing code here
		# use self.draw_<prim_type>s([data]) passing optional data arg 
		# if prims are dynamic 
		self.draw_lines()
		self.draw_quads_wireframe()
		self.flush()
		
	def update(self):
		# do non-graphical updating logic here
		self.rot += 0.1
		
	def keys(self, key, x, y):
		# handle keys here
		pass
		
def main():
	dim = Dimensions(640, 480)
	context = Context(dim.w, dim.h, 3)
	context.loop()
	
if __name__ == '__main__':
	main()

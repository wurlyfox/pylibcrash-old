import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')

from pylibcrashutils.gfx.vbo_context import VBOContext
from pylibcrashutils.gfx.general.geom import *

from OpenGL.GL import *
from OpenGL.GLU import *

class Context(VBOContext):
	def __init__(self, w, h, dimensions=3):
		super().__init__(w, h, dimensions=dimensions, colors_enabled=False)
		# initialize global primitive buffers here
		# also any non-dynamic primitive buffers should be uploaded here
		# with self.upload_<prim_type>(data)
	
	def draw(self):
		self.update()
		gluPerspective(45, self.w/self.h, 0.1, 100.0)
		# do drawing code here
		# use self.draw_<prim_type>s([data]) passing optional data arg 
		# if prims are dynamic 
		
	def update(self):
		# do non-graphical updating logic here
		# also handle keys here
		pass
		
def main():
	dim = Dimensions(640, 480)
	context = Context(dim.w, dim.h, 3)
	context.loop()
	
if __name__ == '__main__':
	main()

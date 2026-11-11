from OpenGL.GL import *
from OpenGL.GLUT import *
from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.general.texture import *

import numpy as np

gl_texture_map = {}		
def using_texture(texture, texid, fn):
	if texture.format.color_fmt != 'ABGR8888':
		texture = texture.convert('ABGR8888')
	width, height = int(texture.dim.w), int(texture.dim.h)
	data = texture.data.ravel()
	if texid not in gl_texture_map:
		gl_texture_map[texid] = glGenTextures(1)
	glActiveTexture(GL_TEXTURE0);
	glBindTexture(GL_TEXTURE_2D, gl_texture_map[texid])
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
		GL_RGBA, GL_UNSIGNED_INT_8_8_8_8, data)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glEnable(GL_TEXTURE_2D)
	fn()
	glDisable(GL_TEXTURE_2D)
	glBindTexture(GL_TEXTURE_2D, 0)

def gl_draw_image(texture, texid, dim_screen, loc=(0,0), dim=None, scale=1, crop=None):
	if not isinstance(loc, Point):
		loc = Point(loc[0], loc[1])
	
	dim = (dim or texture.dim)*scale
	dim_screen.d = 1
	loc = ((loc / dim_screen) * 2) - Point(1,1)
	dim = ((dim / dim_screen) * 2)
	rect = Rect2d(loc, dim)
	quad = rect.to_quad()
	
	src = Rect2d(Point(0,0),Dimensions(1,1))
	if isinstance(crop, Rect2d):
		src.loc = crop.loc / texture.dim
		src.dim = crop.dim / texture.dim
	uvs = src.to_quad()
	
	def draw_quad():
		glBegin(GL_QUADS)
		for vert, uv in zip(quad.verts, uvs.verts):
			glTexCoord2f(uv.x, uv.y)
			glVertex2f(vert.x, -vert.y)
		glEnd()
	using_texture(texture, texid, draw_quad)


"""
  
dir should be (0,0,1) at rot (0,0,0)
    should be (1,0,0) at rot (pi/2,0,0)
    should be (0,0,-1) at rot (pi,0,0)
    should be (-1,0,0) at rot (3pi/2,0,0)
    should be (0,-1,0) at rot (0,pi/2,0)
    should be (0,0,-1) at rot (0,pi,0)
    should be (0,1,0) at rot(0,3pi/2,0)
    
 
    |  /
    | /
    |/   
----+----
   /|
  / |
 /  |
    
"""

class GLCamera:
	def __init__(self):
		self.trans = Point(0,0,0)
		self.rot = Point(0,0,0)
		self.rotvel = Vector(0.001,0.001,0)
		self.dir = Vector(0,0,0)
		self.speed = 0
		
	def update(self, keys):
		self.handle_keys(keys)
		self.dir.x = math.sin(self.rot.x)
		self.dir.y = -math.sin(self.rot.y)
		self.dir.z = -math.cos(self.rot.x)*math.cos(self.rot.y)
		self.trans += self.dir*self.speed
		glTranslatef(self.trans.x, self.trans.y, self.trans.z)
		glRotatef((180/math.pi)*self.rot.x, 0.0, 1.0, 0.0)
		glRotatef((180/math.pi)*self.rot.y, 1.0, 0.0, 0.0)
		glRotatef((180/math.pi)*self.rot.z, 0.0, 0.0, 1.0)
		
	def handle_keys(self, keys):
		if keys[GLUT_KEY_LEFT]:
			self.rot.x -= self.rotvel.x
		elif keys[GLUT_KEY_RIGHT]:
			self.rot.x += self.rotvel.x
		elif keys[GLUT_KEY_UP]:
			self.rot.y += self.rotvel.y
		elif keys[GLUT_KEY_DOWN]:
			self.rot.y -= self.rotvel.y
		if keys[b'a']:
			self.speed = 10
		elif keys[b'z']:
			self.speed = -10
		else:
			self.speed = 0
		

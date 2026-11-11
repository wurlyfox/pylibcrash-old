from OpenGL.GLUT import *
from OpenGL.GL import *
from ctypes import c_float
import numpy as np
from collections import defaultdict

class GLUTContext:

	def __init__(self, w, h):
		self.w = w
		self.h = h
		self.keys = defaultdict(lambda: False)
		self.wind = None
		self.vbo = None
		self.mode = 0
		self.init()

	def init(self):
		glutInit()
		glutInitDisplayMode(GLUT_RGBA)
		glutInitWindowSize(self.w, self.h)
		glutInitWindowPosition(0, 0)
		self.wind = glutCreateWindow("GLUT Context")
		glutKeyboardFunc(self.keydown)
		glutKeyboardUpFunc(self.keyup)
		glutSpecialFunc(self.keydown)
		glutSpecialUpFunc(self.keyup)
		glutDisplayFunc(self.render)
		glutIdleFunc(self.render)

	def print(self, x, y, string):
		glRasterPos2f(x, y)
		for c in string:
			glutBitmapCharacter(GLUT_BITMAP_TIMES_ROMAN_24, ord(c))
					
	def update(self):
		pass
		
	def draw(self):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		if self.mode == 1:
			glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
		elif self.mode == 0:
			glFrustum(-1.0, 1.0, -1.0, 1.0, 1.0, 10000.0)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()

	def render(self):
		self.update()
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glViewport(0, 0, self.w, self.h)
		self.draw()
		glutSwapBuffers()

	def keydown(self, key, x, y):
		self.keys[key] = True
		
	def keyup(self, key, x, y):
		self.keys[key] = False

	def loop(self):
		glutMainLoop()

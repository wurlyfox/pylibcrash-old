from OpenGL.GL import *

def draw_poly2d(poly):
    glBegin(GL_TRIANGLES)
    for v in poly.verts:
        glVertex2f(v.x, v.y)
    glEnd()
    
def draw_poly2d_wireframe(poly):
    glBegin(GL_LINE_LOOP)
    for v in poly.verts:
        glVertex2f(v.x, v.y)
    glEnd()
    
def draw_poly(poly):
    glBegin(GL_TRIANGLES)
    for v in poly.verts:
        glVertex3f(v.x, v.y, v.z)
    glEnd()
    
def draw_poly_wireframe(poly):
    glBegin(GL_LINE_LOOP)
    for v in poly.verts:
        glVertex3f(v.x, v.y, v.z)
    glEnd()

def draw_quad2d(quad):
    glBegin(GL_QUADS)
    for v in quad.verts:
        glVertex2f(v.x, v.y)
    glEnd()

def draw_quad(quad):
    glBegin(GL_QUADS)
    for v in quad.verts:
        glVertex3f(v.x, v.y, v.z)
    glEnd()

def draw_quad_wireframe(quad):
    glBegin(GL_LINE_LOOP)
    for v in quad.verts:
        glVertex3f(v.x, v.y, v.z)
    glEnd()
    
def draw_line2d(line):
    glBegin(GL_LINES)
    for p in line.points:
        glVertex2f(v.x, v.y)
    glEnd()
    
def draw_line(line):
    glBegin(GL_LINES)
    for p in line.points:
        glVertex3f(p.x, p.y, p.z)
    glEnd()

def draw_rect2d(rect):
    quad = rect.to_quad()
    draw_quad2d(quad)

def draw_rect3d(rect):
    faces = rect.get_faces()
    for face in faces:
        quad = face.to_quad()
        draw_quad_wireframe(quad)

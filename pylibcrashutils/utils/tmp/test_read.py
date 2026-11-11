import cProfile, pstats
import sys

sys.path.append('/home/user/src/pylibcrash')

from libcrash import lib, ffi

from pylibcrash.nsd import Nsd
from pylibcrash.nsf import Nsf
from pylibcrash.page import Page, TexturePage
from pylibcrash.entry import Entry, Eid #, Item
from pylibcrash.formats.zdat import Zone

from OpenGL.GL import *
from gfx.vbo_context import VBOContext
from gfx.scene import Scene

import numpy as np

from ctypes import POINTER, c_long

def clamp(v, a, b):
	return min(max(v, a), b)
def wrap(v, a, b):
	return a if v > b else b if v < a else v

def entry_find_type(nsf, type):
	entries = []
	pages = [page for page in nsf.pages if not isinstance(page, TexturePage)]
	pages.pop()
	for page in pages:
		print(page.type)
		entries.extend([entry for entry in page.entries if entry.type == type])
	return entries

def find_zone_world(nsf, eid):
	zones = entry_find_type(nsf, 7)
	for zone in zones:
		world = [world for world in zone.worlds if world == eid]
		if len(world) > 0: 
			world = world[0]
			break
	return zone, world
	
class Context(VBOContext):
	def __init__(self, nsf, w, h):
		self.profiler = cProfile.Profile()
		self.profiler.enable()
		super().__init__(w, h)
		zone, world = find_zone_world(nsf, Eid("1__9W"))
		print(str(zone.eid))
		self.render_w = 320
		self.render_h = 224
		self.nsf = nsf  # should this be part of the context?
		self.scene = Scene(nsf, zone, 
						   self.render_w, self.render_h)
		self.draw_mode = 0
		
	def draw_polys(self, polys, color=None, wireframe=False):
		if color=="blue":
			glColor3f(0.0,0.0,1.0)
		elif color=="green":
			glColor3f(0.0,1.0,0.0)
		elif color=="blue":
			glColor3f(0.0,0.0,1.0)
		else:
			glColor3f(1.0,1.0,1.0)
			
		verts = polys.view(np.float32)
		poly_count = len(polys)
		if wireframe:
			super().draw_polys_wireframe(verts, poly_count)
		else:
			super().draw_polys(verts, poly_count)
			
	def update(self):
		self.scene.project(self.nsf)
		self.draw_polys(self.scene.polys, wireframe=True)
		
	def update_diffs(self):
		self.scene.project(self.nsf)
		
		scene = Scene(self.nsf, self.scene.zone, 
					  self.render_w, self.render_h)
		scene.path_idx = self.scene.path_idx
		scene.path_pt_idx = self.scene.path_pt_idx
		scene.cam_trans = self.scene.cam_trans
		scene.cam_rot = self.scene.cam_rot
		scene.compute_visible_polys(self.nsf, self.render_w, self.render_h)
		scene.project(self.nsf)
		
		# diff_a = self.scene - scene
		# diff_b = scene - self.scene
		# diff_b.path_idx = self.scene.path_idx
		# diff_b.path_pt_idx = self.scene.path_pt_idx
		
		if self.draw_mode == 0:
			scene_shaded = scene
		elif self.draw_mode == 1:
			scene_shaded = self.scene
		# elif self.draw_mode == 2:
			# scene_shaded = diff_a
		# elif self.draw_mode == 3:
			# scene_shaded = diff_b
		
		self.draw_polys(scene_shaded.polys, "blue", wireframe=True)
		
		# if self.draw_mode < 2:
			# draw_polys(diff_a.polys, "blue", wireframe=True)
			# draw_polys(diff_b.polys, "green", wireframe=True)                 
		
	def draw(self):
		super().draw()
		self.update()
		# self.update_diffs()
		self.flush()

	def keys(self, key, x, y):
		path_idx = self.scene.path_idx
		path_pt_idx = self.scene.path_pt_idx
		if key == b'a':
			self.scene.update_path(self.nsf, path_idx, path_pt_idx+1)
		if key == b'z':
			self.scene.update_path(self.nsf, path_idx, path_pt_idx-1)
		if key == b's':
			self.scene.update_path(self.nsf, path_idx+1, 0)
		if key == b'x':
			self.scene.update_path(self.nsf, path_idx-1, 0)
		if key == b'm':
			self.draw_mode = wrap(self.draw_mode+1, 0, 3)
		if key == b'd':
			self.scene.screen_offset.z = wrap(self.scene.screen_offset.z+1,20,0x800)
		if key == b'c':
			self.scene.screen_offset.z = wrap(self.scene.screen_offset.z-1,20,0x800)
		if key == b'n':
			self.profiler.disable()
			stats = pstats.Stats(self.profiler).sort_stats('ncalls')
			stats.print_stats()
			stats.dump_stats('out.prof')
			
def main():
	with open("S0000009.NSD", "rb") as nsd_file:
		nsd_data = nsd_file.read()
	with open("S0000009.NSF", "rb") as nsf_file:
		nsf_data = nsf_file.read()
	nsd = Nsd.from_cbytes(nsd_data)
	nsf = Nsf.from_cbytes(nsf_data, nsd)
	# needed now for interfacing with c code
	lib.nsd_read(nsd.cbytes)
	lib.nsf_read(nsf.cbytes, nsd.cptr)
	context = Context(nsf, 640, 480)
	context.loop()
	
if __name__ == '__main__':
	main()

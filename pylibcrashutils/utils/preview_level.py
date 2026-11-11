import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')

from libcrash import lib, ffi

from pylibcrash.nsd import Nsd
from pylibcrash.nsf import Nsf
from pylibcrash.page import Page, TexturePage
from pylibcrash.entry import Entry, Eid #, Item
from pylibcrash.formats.zdat import Zone

from pylibcrashutils.gfx.scene import Scene
from pylibcrashutils.gfx.scene_unprocessed import SceneUnprocessed
from pylibcrashutils.gfx.general.geom_comp import *
from pylibcrashutils.gfx.general.texture import *
from pylibcrashutils.gfx.gl.geom import *
from pylibcrashutils.gfx.gl.glut_context import *
from pylibcrashutils.gfx.gl.util import *
from pylibcrashutils.gfx.vbo_context import VBOContext
#from pylibcrashutils.gfx.rasterize import clip_polys

from pylibcrash.formats.slst import PolyId

from pylibcrashutils.build import ns_read

from OpenGL.GLUT import *

import pickle
import pandas as pd
from collections import defaultdict

def flatten(lst):
	lst = sum([flatten(item) if isinstance(item, list) else [item]
			  for item in lst], [])
	return lst

def wrap(v, a, b):
	return a if v > b else b if v < a else v

def ndefaultdict():
	return defaultdict(ndefaultdict)
	
def inttofloat(flt):
	tmp=np.array([flt], dtype=np.float32)
	tmp=tmp.view(dtype=np.uint32)
	return tmp[0].astype(np.float32)
	
class ContextProcessed(VBOContext):
	def __init__(self, nsf, w, h):
		super().__init__(w, h, dimensions=2, indexed=False, colors_enabled=False)
		self.zone_idx = 0
		self.zones = [entry for page in nsf.pages
							if page.type != 1
							for entry in page.entries 
							if entry.type == 7]
		self.zones.sort(key=lambda e: e.eid.value)
		self.scene = Scene(nsf, self.zones[0], w, h)
		self.scene.path_idx = 0
		self.progress = 0
		self.enable_gl_proj = True
		self.debug_gfx = False
		self.debug_info = ndefaultdict()
		region = Rect2d(Point(256,256), Dimensions(512,256)) 
		self.crop = region
		
		
	def draw(self):
		super().draw()
		glColor3f(1.0, 1.0, 1.0)
		#glScalef(self.scene.screen_offset.x*2/320, 
		#         self.scene.screen_offset.y*2/224, 1.0)
		#glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
		#self.print(-0.5,-0.5, f"current path: {self.scene.path_idx}\n"
		#				+  f"current point: {self.scene.path_pt_idx}\n")
		
		if self.debug_gfx:
			self.get_debug_info()
		self.scene.compute_visible_polys(1024, 512)
		self.scene.project(normalize=True)
		for poly in self.scene.polys:
			for vert in poly.verts:
				# vert.x = ((inttofloat(vert.x)/self.scene.screen_offset.x)-1.0)*2
				# vert.y = -((inttofloat(vert.y)/self.scene.screen_offset.y)-1.0)*3
				vert.x = vert.x*2
				vert.y = -vert.y*3
		
		polys, poly_ids = zip(*[(poly, poly_id) for poly, poly_id in 
								list(zip(self.scene.polys, self.scene.poly_ids))
								if poly_id == PolyId(1, 0x74)])
		#polys = np.array([poly for poly in self.scene.polys
		#				  if not any(vert.z==0.0 for vert in poly.verts)])
		polys = np.array(polys)
		poly_ids = np.array(poly_ids)
		
		
		# if self.enable_gl_proj:
			# self.dimensions = 3
			# for poly in polys:
				# for vert in poly.verts:
					# ox = self.scene.screen_offset.x
					# oy = self.scene.screen_offset.y
					# vert.x = (((vert.x + 1.0)*ox)-ox)/t_vert.z
					# vert.y = (((1.0 - vert.y)*oy)-oy)/t_vert.z
		
		
		zbuf = self.scene.get_zbuf(1024, 512)
		texture = Texture(None, Dimensions(1024, 512), zbuf)
		dim = Dimensions(self.w, self.h)
		crop = self.crop
		gl_draw_image(texture, 1, dim, dim=dim, crop=crop)
		self.print(0,0,f"{crop.loc.x}, {crop.loc.y}, {crop.dim.w}, {crop.dim.h}")
		for poly, poly_id in zip(polys, poly_ids):
			val = ffi.cast("uint16_t *", poly_id.cptr)[0]
			ctr = sum(poly.verts, Point(0,0,0))/3
			ctr.x = (ctr.x)
			ctr.y = (ctr.y)+0
			self.print(max(min(ctr.x,1.0),-1.0), max(min(ctr.y,1.0),-1.0), f"{val:04X}")
			self.print(max(min(poly.verts[0].x,1.0),-1.0), 
			           max(min(poly.verts[0].y,1.0),-1.0),f"{poly.verts[0].z}")
			self.print(max(min(poly.verts[1].x,1.0),-1.0),
			           max(min(poly.verts[1].y,1.0),-1.0),f"{poly.verts[1].z}")
			self.print(max(min(poly.verts[2].x,1.0),-1.0),
			           max(min(poly.verts[2].y,1.0),-1.0),f"{poly.verts[2].z}")
			
		
		#glBegin(GL_TRIANGLES)
		#glVertex2f(-1.0,-1.0)
		#glVertex2f(1.0,-1.0)
		#glVertex2f(-1.0,1.0)
		#glEnd()
		#self.draw_polys(polys)
		self.draw_polys_wireframe(polys)
	
		self.flush()
		
	def update(self):
		inc_val = 1
		delta_progress = 0
		if self.keys[b'a']:
			delta_progress = -inc_val
		elif self.keys[b'd']:
			delta_progress = inc_val
		elif self.keys[b'z']:
			self.polys_to_csv()
		elif self.keys[GLUT_KEY_UP]:
			if self.keys[b'q'] == False:
				self.crop.loc.y -= 10
			else:
				self.crop.dim.h -= 10
		elif self.keys[GLUT_KEY_DOWN]:
			if self.keys[b'q'] == False:
				self.crop.loc.y += 10
			else:
				self.crop.dim.h += 10
		elif self.keys[GLUT_KEY_LEFT]:
			if self.keys[b'q'] == False:
				self.crop.loc.x -= 10
			else:
				self.crop.dim.w -= 10
		elif self.keys[GLUT_KEY_RIGHT]:
			if self.keys[b'q'] == False:
				self.crop.loc.x += 10
			else:
				self.crop.dim.w += 10
		if delta_progress:
			self.update_state(delta_progress)
			
	def update_state(self, delta_progress):
		"""
		updates the current (zone, path, path point) given a change in 
		'progress' (number of path points to move forward or back)
		"""
		new_progress = self.scene.path_pt_idx + delta_progress
		
		# scene currently renders only (the worlds of and from path of)
		# one zone at a time. so we have to change that current zone to
		# a neighbor zone when boundary conditions are met
		if self.scene.path_idx == 0 and \
				new_progress < 0 and \
				self.zone_idx > 0:
			self.zone_idx -= 1
			self.scene.zone = self.zones[self.zone_idx]
			self.scene.path_pt_idx = len(self.scene.zone.paths[-1].points)-1
			self.scene.path_idx = len(self.scene.zone.paths)-1
			self.scene.update_poly_ids(self.scene.path_idx, 
				self.scene.path_pt_idx, 'forward')
		elif self.scene.path_idx == len(self.scene.zone.paths)-1 and \
				new_progress >= len(self.scene.zone.paths[-1].points)-1 and \
				self.zone_idx < len(self.zones):
			self.zone_idx += 1
			self.scene.zone = self.zones[self.zone_idx]
			self.scene.path_pt_idx = 0
			self.scene.path_idx = 0
			self.scene.update_poly_ids(self.scene.path_idx, 
				self.scene.path_pt_idx, 'backward')
		else:
			self.scene.update_path(self.scene.path_idx, new_progress)
				
	
	def get_debug_info(self):
		def parse_vec(line):
			return [int(c) for c in line.split(",")]
		def parse_mat(lines):
			return [parse_vec(line) for line in lines]
		with open("temp_gfx.txt", "r") as infile:
			lines = infile.readlines()
		cam_trans = parse_vec(lines[0])
		cam_rot = parse_vec(lines[1])
		m_cam_rot = parse_mat(lines[2:5])
		ms_cam_rot = parse_mat(lines[5:8])
		scene = self.scene
		info = self.debug_info[scene.zone.eid][scene.path_idx][scene.path_pt_idx]
		info['cam_trans'] = cam_trans
		info['cam_rot'] = cam_rot
		info['m_cam_rot'] = m_cam_rot
		info['ms_cam_rot'] = ms_cam_rot
		prev = False
		for line in lines[8:]:
			values = line.split(',')
			
			if len(values) == 3:
				if prev == False:
					u_viewmodel = parse_vec(line)
					prev = True
				else:
					r_viewmodel = parse_vec(line)
					prev = False
				continue
			for i in range(14):
				values[i] = int(values[i])
			for i in range(14,17):
				values[i] = float(values[i])
			poly_id = values[0]
			vert_idx = values[1]
			info[poly_id]['u_viewmodel'] = u_viewmodel
			info[poly_id]['r_viewmodel'] = r_viewmodel
			info[poly_id][vert_idx] = values[2:17]
			
	def polys_to_csv(self):
		# rows = []
		# scene = self.scene
		# for poly, poly_id in zip(self.scene.polys, self.scene.poly_ids):
			# poly_id_val = (poly_id.world_idx << 12 | poly_id.poly_idx)
			# v0x = ((poly.verts[0].x+1)*self.scene.screen_offset.x)
			# v0y = ((poly.verts[0].y+1)*self.scene.screen_offset.y)
			# v1x = ((poly.verts[1].x+1)*self.scene.screen_offset.x)
			# v1y = ((poly.verts[1].y+1)*self.scene.screen_offset.y)
			# v2x = ((poly.verts[2].x+1)*self.scene.screen_offset.x)
			# v2y = ((poly.verts[2].y+1)*self.scene.screen_offset.y)
			# row = [str(scene.zone.eid), scene.path_idx, scene.path_pt_idx,
			       # f'{poly_id_val:04X}', 
			       # v0x, v0y, poly.verts[0].z,
			       # v1x, v1y, poly.verts[1].z,
			       # v2x, v2y, poly.verts[2].z]
			# rows.append(row)
		# columns = ['zone', 'path', 'path_pt', 'poly_id', 
				   # 'v0x', 'v0y', 'v0z', 
				   # 'v1x', 'v1y', 'v1z', 
				   # 'v2x', 'v2y', 'v2z']
		# df = pd.DataFrame(rows, columns=columns)
		# df.to_csv("output.csv")
		def vec_cols(vec):
			return [vec+".x", vec+".y", vec+".z"]
		def mat_cols(mat):
			return sum([vec_cols(m) for m in 
						[mat+'[0]', mat+'[1]', mat+'[2]']], [])	
		rows = []
		for zone_eid, zone_map in self.debug_info.items():
			for path_idx, path_map in zone_map.items():
				for path_pt_idx, point_map in path_map.items():
					cam_trans = point_map['cam_trans']
					cam_rot = point_map['cam_rot']
					m_cam_rot = point_map['m_cam_rot']
					ms_cam_rot = point_map['ms_cam_rot']
					del point_map['cam_trans']
					del point_map['cam_rot']
					del point_map['m_cam_rot']
					del point_map['ms_cam_rot']
					for poly_id, poly_map in point_map.items():
						u_viewmodel = poly_map['u_viewmodel']
						r_viewmodel = poly_map['r_viewmodel']
						del poly_map['u_viewmodel']
						del poly_map['r_viewmodel']
						for vert_idx, vert in poly_map.items():
							row = [str(zone_eid), path_idx, path_pt_idx, \
								   poly_id, vert_idx] + \
								   cam_trans + cam_rot + \
								   m_cam_rot[0] + m_cam_rot[1] + m_cam_rot[2] + \
								   ms_cam_rot[0] + ms_cam_rot[1] + ms_cam_rot[2] + \
								   u_viewmodel + r_viewmodel + vert
							rows.append(row)
		columns = ['zone', 'path', 'path_pt', 'poly_id', 'vert_idx'] \
				 + vec_cols('cam_trans') + vec_cols('cam_rot') \
				 + mat_cols('m_cam_rot') + mat_cols('ms_cam_rot') \
				 + sum([vec_cols(v) for v in ['u_view_model', 'r_viewmodel', \
					'w_vert', 'u_vert', 'r_vert', 'v_vert', 's_vert']], [])
		df = pd.DataFrame(rows, columns=columns)
		df.to_csv("output.csv")
		
class Context(VBOContext):
	def __init__(self, scene, w, h):
		glEnable(GL_DEPTH_CLAMP)
		super().__init__(w, h, dimensions=3, indexed=False, colors_enabled=False)
		self.scene = scene
		#self.rects = [rect for rect in 
		#              sum([flatten(zone.octree) for zone in scene.zones], [])
		#              if rect is not None]
		self.angle = 0
		self.point = Point(0, 0, 0)
		self.progress = 0.0
		self.upload_all()

	def upload_all(self):
		lines = np.array(self.scene.lines)
		polys = np.array(self.scene.polys)
		#quads = np.array(sum([rect.quads for rect in self.rects], []) +
		#                 sum([zone.bound.quads for zone in self.scene.zones], []),
		#                 dtype=Quad)
		self.upload_lines(lines)
		self.upload_polys(polys)
		#self.upload_quads(quads)
		
	def update(self):
		inc_val = 0.01
		if self.keys[b'a']:
			self.point.x -= inc_val
		elif self.keys[b'd']:
			self.point.x += inc_val
		elif self.keys[b'w']:
			self.point.y += inc_val
		elif self.keys[b's']:
			self.point.y -= inc_val
		elif self.keys[b'q']:
			self.point.z -= inc_val
		elif self.keys[b'e']:
			self.point.z += inc_val
		# elif self.keys[b'z']:
		#	self.p_idx = clamp(p_idx - 1, 0, len(self.scene.worlds) - 1)
		# elif self.keys[b'x']:
		#	self.p_idx = clamp(self.p_idx + 1, 0, len(self.scene.worlds) - 1)

	def draw(self):
		glutSetWindow(self.wind)
		super().draw()
		glColor3f(1.0, 1.0, 1.0)
		glScalef(10.0,10.0,10.0)
		glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

		#self.angle += ((2 * math.pi) / 180)
		#glRotatef(self.angle, 1.0, 0.5, 0.0)
		self.progress = wrap(self.progress + 0.1, 0, len(self.scene.lines)-1)
		p_idx = math.floor(self.progress)
		t = self.progress - p_idx
		path_line = self.scene.lines[p_idx]
		camera = (path_line.points[0]*(1-t)) + (path_line.points[1]*t)
		camera += self.point
		#glRotatef(180.0, 1.0, 0.0, 0.0)
		#glRotatef(180.0, 0.0, 0.0, 1.0)
		glTranslatef(-camera.x, -camera.y, -camera.z)

		glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
		# line = Line([Point(0, 0, 0), self.point])
		# draw_line(line)
		# cube = Rect3d(Point(0.25, 0.25, 0.25), Dimensions(0.5, 0.5, 0.5))
		# draw_rect3d(cube)
		# poly = Poly([self.point,
		#              Point(0.5, 0.5, 0.5),
		#              Point(0.25, 0.5, 0.5)])
		# draw_poly(poly)
		# intersection = cube.find_poly_intersection(poly)
		# if intersection:
		#     pad_cube = intersection.pad_rect3d(Dimensions(0.1, 0.1, 0.1))
		#     draw_rect3d(pad_cube)
		self.draw_lines()
		self.draw_polys()
		#self.draw_quads_wireframe(upload=False)
		
		# cubes = split_rect3d(get_polys_bound(self.polys), [2, 0, 2])
		# for cube in cubes:
		#     draw_rect3d(cube)
		# group = self.groups[self.p_idx]
		# for poly in group:
		#    draw_poly(poly)
		
class ZBufContext(GLUTContext):
	def __init__(self, scene, w, h):
		super().__init__(w, h)
		self.scene = scene
		
	def draw(self):
		glutSetWindow(self.wind)
		super().draw()
		zbuf = self.scene.get_zbuf(512, 256)
		texture = Texture(None, Dimensions(512, 256), zbuf)
		gl_draw_image(texture, 0, Dimensions(self.w, self.h))
	
def preview_level(nsf_path, w, h):
	nsd_path = nsf_path[:-1] + 'D'
	with open(nsf_path, "rb") as nsf_file:
		nsf_data = nsf_file.read()
	with open(nsd_path, "rb") as nsd_file:
		nsd_data = nsd_file.read()
	nsd = Nsd.from_cbytes(nsd_data)
	nsf = Nsf.from_cbytes(nsf_data, nsd)
	lib.nsd_read(nsd.cbytes)
	lib.nsf_read(nsf.cbytes, nsd.cptr)
	context_processed = ContextProcessed(nsf, w, h)
	context_processed.mode = 1
	
	#zbuf_context = ZBufContext(context_processed.scene, w, h)
	
	context_processed.loop()
	
def preview_level_unprocessed(path, w, h):
	with open(path, "rb") as scene_file:
		scene = pickle.load(scene_file)
	scene.pickle_fix()
	context = Context(scene, w, h)
	context.mode = 0
	context.loop()
	
def main():
	w, h = 1024, 768
	nsf_path = "./gen_level/S0000001.NSF"
	#nsf_path = "/home/user/src/pylibcrashutils/nsf/S0/S0000009.NSF"
	scene_path = "./scene.pk"
	processed = True
	
	if processed:
		preview_level(nsf_path, w, h)
	else:
		preview_level_unprocessed(scene_path, w, h)
	
if __name__ == '__main__':
	main()

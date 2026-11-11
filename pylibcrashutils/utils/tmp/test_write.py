import os
import sys
sys.path.append('/home/user/src/pylibcrash')

from libcrash import lib, ffi

from pylibcrash.nsd import Nsd
from pylibcrash.nsf import Nsf
from pylibcrash.page import Page, TexturePage
from pylibcrash.entry import Entry, Eid #, Item
from pylibcrash.formats.zdat import Zone

from gfx.scene import Scene
from gfx.scene_unprocessed import SceneUnprocessed
from gfx.general.geom_comp import *

from gfx.gl.geom import *
from gfx.vbo_context import VBOContext

from gfx.rasterize import clip_polys

from OpenGL.GLUT import *

import pickle

from temp_clip_test import clip_polys_alt

def clamp(v, a, b):
	return min(max(v, a), b)


def wrap(v, a, b):
	return a if v > b else b if v < a else v


def y_func(x, z):
	y = (math.sin(x * 2 * math.pi) + math.cos(z * 2 * math.pi)) / 5
	# z = -10 + (5 * math.sin(x / 10) + 22 * math.cos(y / 10) + \
	#    23 * math.sin(x / 20) + 20 * math.cos(y / 20) + \
	#    50 * math.sin(x / 40) + 20 * math.cos(y / 40) + \
	#    (20 * math.sin(x / 100) * 5 * math.cos(y / 70)))/5
	return y


def draw_line_head(line):
	v = [None] * 3
	slope = line.to_vec()
	perp = Vector(1, 1, -(slope.x + slope.y) / slope.z)
	slope = slope.normalize()
	perp = perp.normalize()
	v[1] = line.points[1]
	sect = v[1] - slope * 0.025
	v[0] = sect + perp * 0.025 / 2
	v[2] = sect - perp * 0.025 / 2
	poly = Poly(v, [1,1,1])
	draw_poly(poly)

# this is the function which procedurally generates world polygons

def generate_polys(res, size):
	polys = []
	v = [0, 0, 0, 0]
	for z in range(-res, res):
		z = (z / res) #*size
		for x in range(-res, res):
			x = (x / res) #*size
			f = (1 / res) #*size
			v[0] = Point(x, y_func(x, z), z)
			v[1] = Point(x + f, y_func(x + f, z), z)
			v[2] = Point(x, y_func(x, z + f), z + f)
			v[3] = Point(x + f, y_func(x + f, z + f), z + f)
			v[0] = v[0] * size
			v[1] = v[1] * size
			v[2] = v[2] * size
			v[3] = v[3] * size
			
			polys.append(Poly([v[0], v[1], v[2]], [1,1,1]))
			polys.append(Poly([v[2], v[1], v[3]], [1,1,1]))
			x = (x * res) #/size
		z = (z * res) #/size
		
	for poly in polys:
		for vert in poly.verts:
			vert.x = vert.x
			vert.y = -vert.y
			vert.z = -vert.z
	return polys

# ... and the function which procedurally generates the level paths
def generate_path(res, size):
	lines = []
	p = [0, 0]
	for z in range(-res, res):
		z = (z / res) #*size
		f = (1 / res) #*size
		x = math.sin(z * 2 * math.pi) / 24 
		x2 = math.sin((z + f) * 2 * math.pi) / 24
		#p[0] = Point(x, y_func(x, z) * 0.5, z)
		#p[1] = Point(x2, y_func(x2, z + f) * 0.5, z + f)
		p[0] = Point(x, 0.5, z)
		p[1] = Point(x2, 0.5, z + f)
		
		
		p[0] = p[0]*size
		p[1] = p[1]*size
		lines.append(Line([p[0], p[1]]))
		z = (z) * res
	for line in lines:
		for point in line.points:
			point.y = -(point.y-6.0)
			point.z = -point.z
	return lines


def scene_build(gen_res, gen_size, world_res, zone_res, path_res, pad):
	scene = SceneUnprocessed.generate(generate_polys, generate_path, gen_res, gen_size)
	scene.compute_worlds(world_res)
	scene.compute_zones(zone_res, path_res, pad)
	return scene
	
def ns_build(scene, lid):
	id_map = { "Will": 0, 
			   "Wil9": None, 
			   "Doct": 5, 
			   "Shad": 29, 
			   "Warp": 32, 
			   "Disp": 4, 
			   "Frui": 3, 
			   "Boxs": 34 }
	extension_map = { 0: 'none',
	                  1: 'svtx', 2: 'tgeo', 3: 'wgeo', 4: 'slst',
					  5: 'tpag', 6: 'ldat', 7: 'zdat', 8: 'cpat',
					  9: 'binf', 10:'opat', 11:'gool', 12:'adio',
					  13:'midi', 14:'inst', 15:'imag', 16:'link',
					  17:'mdat', 18:'ipal', 19:'pbak', 20:'cvtx'}
	def get_essential_entries():
		# load all global, non-procedurally-generated, essential entries
		root_dir = "/home/user/src/pylibcrash/utils/extracted/essential"
		paths = []
		entries = []
		for name in id_map:
			dir = f"{root_dir}/{name}"
			paths.append(f"{dir}C.gool")
			if os.path.exists(dir):
				names = os.listdir(dir)
				_paths = [dir + '/' + name for name in names]
				paths.extend(_paths)
		for path in paths:
			with open(path, "rb") as entry_file:
				entry_data = entry_file.read()
			entry = Entry.from_cbytes(entry_data)
			entry.data_tmp = entry_data
			entries.append(entry)
		return entries
		
	def get_zone_path_spawn(entries):
		for zone_spawn in [entry for entry in entries if entry.type == 7]:
			for entity in zone_spawn.entities:
				if entity.type == 0: break
				entity = None
			if entity: break
			zone_spawn = None
		if zone_spawn is None or entity is None:
			return None, None
		path_spawn = None
		closest_dist = 99999999
		spawn = Point(*entity.path_points[0])
		for path in zone_spawn.paths:
			for point in path.points:
				point = Point(point.x, point.y, point.z)
				dist = Vector.from_point(spawn - point).magnitude()
				if dist >= closest_dist: continue
				path_spawn = path
				closest_dist = dist
		return zone_spawn, path_spawn
	
	def get_ldat_image_data():
		path = "/home/user/src/pylibcrash/utils/ldat_image.bin"
		with open(path, "rb") as image_file:
			image_data = image_file.read()
		image_buffer = np.frombuffer(image_data, dtype=np.uint8)
		return image_buffer

	entries = get_essential_entries() + scene.process()
	for entry in entries:
		if entry.type > 20: continue	
		if not entry.packed: entry.pack()
		path = f"./output/{str(entry.eid)}.{extension_map[entry.type]}"
		with open(path, "wb") as entry_file:
			entry_file.write(entry.bytes)
	
	zone_spawn, path_spawn = get_zone_path_spawn(entries)
	
	nsd = Nsd()
	nsf = Nsf.from_entries(entries, nsd)
	ldat = nsd.ldat
	ldat.lid = lid
	ldat.zone_spawn = zone_spawn.eid
	ldat.path_spawn = list(zone_spawn.paths).index(path_spawn)
	ldat.screen_proj = 0x5A # todo: pass through to SceneUnprocessed
	for name, id in id_map.items():
		if id is None: continue
		ldat.exec_map[id] = Eid(name+'C')

	ldat.image_data = get_ldat_image_data()
		
	return nsf, nsd
	
def flatten(lst):
	lst = sum([flatten(item) if isinstance(item, list) else [item]
			  for item in lst], [])
	return lst

class ContextProcessed(VBOContext):
	def __init__(self, nsf, w, h):
		super().__init__(w, h, dimensions=2, indexed=False)
		self.zone_idx = 0
		self.zones = [entry for page in nsf.pages
							if page.type != 1
							for entry in page.entries 
							if entry.type == 7]
		self.zones.sort(key=lambda e: e.eid.value)
		self.scene = Scene(nsf, self.zones[0], w, h)
		self.scene.path_idx = 0
		self.progress = 0
		
	def draw(self):
		super().draw()
		glColor3f(1.0, 1.0, 1.0)
		glScalef(self.scene.screen_offset.x*2/320, 
		         self.scene.screen_offset.y*2/224, 1.0)
		#glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
		#self.print(-0.5,-0.5, f"current path: {self.scene.path_idx}\n"
		#				+  f"current point: {self.scene.path_pt_idx}\n")

		#self.scene.all_poly_ids()
		self.scene.project()
		self.scene.polys = [poly for poly in self.scene.polys
							if sum(vert.z for vert in poly.verts) > 1000.0]
							
		polys = np.array(self.scene.polys)
		self.draw_polys(polys)
		self.draw_polys_wireframe(polys)
		self.flush()
		
	def update_zone(self, delta_progress):
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
				
	def keys(self, key, x, y):
		inc_val = 1
		delta_progress = 0
		if key == b'a':
			delta_progress = -inc_val
		elif key == b'd':
			delta_progress = inc_val
		if delta_progress:
			self.update_zone(delta_progress)
		
class Context(VBOContext):
	def __init__(self, scene, w, h):
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
		
	def draw(self):
		super().draw()
		glColor3f(1.0, 1.0, 1.0)
		glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

		#self.angle += ((2 * math.pi) / 180)
		#glRotatef(self.angle, 1.0, 0.5, 0.0)
		self.progress = wrap(self.progress + 1, 0, len(self.scene.lines)-1)
		p_idx = math.floor(self.progress)
		t = self.progress - p_idx
		path_line = self.scene.lines[p_idx]
		camera = (path_line.points[0]*(1-t)) + (path_line.points[1]*t)
		camera += self.point
		glRotatef(0, 1.0, 0.0, 0.0)
		glRotatef(0, 0.0, 0.0, 1.0)
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
		#self.draw_quads_wireframe()
		
		# cubes = split_rect3d(get_polys_bound(self.polys), [2, 0, 2])
		# for cube in cubes:
		#     draw_rect3d(cube)
		# group = self.groups[self.p_idx]
		# for poly in group:
		#    draw_poly(poly)
		
	def keys(self, key, x, y):
		inc_val = 0.01
		if key == b'a':
			self.point.x -= inc_val
		elif key == b'd':
			self.point.x += inc_val
		elif key == b'w':
			self.point.y += inc_val
		elif key == b's':
			self.point.y -= inc_val
		elif key == b'q':
			self.point.z -= inc_val
		elif key == b'e':
			self.point.z += inc_val
		# elif key == b'z':
		#	self.p_idx = clamp(p_idx - 1, 0, len(self.scene.worlds) - 1)
		# elif key == b'x':
		#	self.p_idx = clamp(self.p_idx + 1, 0, len(self.scene.worlds) - 1)

# it takes quite a while to compute the octrees. i have the resolution 
# up higher than normal at the moment

# in the mean time we can look at some of the code which is generating
# the worlds/zones/etc.

def main():
	build_scene = True
	build_ns = True
	
	lid = 1
	gen_res = 8
	gen_size = 8
	world_res = [2, 1, 2]
	zone_res = 5
	path_res = 6
	pad = Dimensions(0.4, 1.0, 0.0)
	
	filename = f"S{lid:07X}"
	nsd_filename = filename + ".NSD"
	nsf_filename = filename + ".NSF"
	
	nsf, nsd = None, None
	if build_ns:
		if not os.path.exists("scene.pk") or build_scene == True:
			scene = scene_build(gen_res, gen_size, world_res, zone_res, path_res, pad)
			with open("scene.pk", "wb") as scene_file:
				pickle.dump(scene, scene_file)
		else:
			with open("scene.pk", "rb") as scene_file:
				scene = pickle.load(scene_file)
			scene.pickle_fix()
		
		nsf, nsd = ns_build(scene, lid)
		nsd.pack()
		nsf.pack()
		with open(nsf_filename, "wb") as nsf_file:
			nsf_file.write(nsf.bytes)
		with open(nsd_filename, "wb") as nsd_file:
			nsd_file.write(nsd.bytes)
	else:
		with open(nsf_filename, "rb") as nsf_file:
			nsf_data = nsf_file.read()
		with open(nsd_filename, "rb") as nsd_file:
			nsd_data = nsd_file.read()
		nsd = Nsd.from_cbytes(nsd_data)
		nsf = Nsf.from_cbytes(nsf_data, nsd)
		
	with open("scene.pk", "rb") as scene_file:
		scene = pickle.load(scene_file)
	scene.pickle_fix()
	# create a context to render the geometry in the generated nsf/nsd 
	# files 
	# proper rendering here ensures that it will render correctly in-game
	w, h = 1024, 768
	lib.nsd_read(nsd.cbytes)
	lib.nsf_read(nsf.cbytes, nsd.cptr)
	context_processed = ContextProcessed(nsf, w, h)
	context_processed.mode = 1
	context_processed.loop()

	#context = Context(scene, w, h)
	#context.mode = 0
	#context.loop()
	
if __name__ == '__main__':
	main()

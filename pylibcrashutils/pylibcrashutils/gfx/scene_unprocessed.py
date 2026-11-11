import random
import math
from pylibcrashutils.general.list import *

from pylibcrashutils.gfx.scene import Scene
from pylibcrashutils.gfx.fixed_pt import float_to_fixed, radians_to_ang10

from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.general.geom_comp import *
from pylibcrashutils.gfx.general.texture import *

from pylibcrash.formats.wgeo import *
from pylibcrash.formats.slst import *
from pylibcrash.formats.zdat import *

from pylibcrash.page import Page, TexturePage


def pickle_fix_point(point):
	new_point = Point(point['x'], point['y'], point['z'])
	return new_point

def pickle_fix_dimensions(dim):
	new_dimensions = Dimensions(dim['x'], dim['y'], dim['z'])
	return new_dimensions
	
def pickle_fix_line(line):
	new_line = Line(line[0])
	return new_line
	
def pickle_fix_poly(poly):
	new_poly = Poly(poly['verts'], poly['vertuvws'], poly['texid'])
	return new_poly
	
def pickle_fix_bound(bound):
	bound.loc = pickle_fix_point(bound.loc)
	bound.dim = pickle_fix_dimensions(bound.dim)
	return bound
	
def compute_inverse_fw_map():
	"""
	Computes the 24 permutations of vertex coordinates of a unit size 
	right triangle, as ordered in each of the 25 sections of the 
	texcoord region map in the Crash games.
	"""
	
	# (0,0), (1,0), (0,1)
	# (0,0), (1,0), (1,1)
	# (1,0), (1,1), (0,1)
	# (0,0), (1,1), (0,1)
	
	
	idxes_encoded = 0x49769A
	d = idxes_encoded
	coords = [d := d >> 1 for _ in range(24)]
	coords = [v & 1 for v in coords][::-1]
	coords = list(zip(coords[0::2], coords[1::2]))
	coords = [list(d) for d in zip(*(coords[i::3] for i in range(3)))]
	def perms(lst):
		if len(lst) == 1:
			return [[lst[0]]]
		return [[lst[idx]] + perm for idx in range(len(lst))
				for perm in perms(lst[:idx]+lst[idx+1:])]
	coords = sum([perms(coord) for coord in coords], [])
	for i in range(0,24,6):
		coords[i+2], coords[i+3] = coords[i+3], coords[i+2]
	inv_fw_map = {tuple(coord): idx for idx, coord in enumerate(coords)}
	return inv_fw_map
inv_fw_map = compute_inverse_fw_map()
	
def uvs_to_texinfo(vertuvws):
	"""
	Converts normalized uv coordinates to a texinfo.
	
	The unnormalized coordinates must describe a right-triangle of 
	width and height which are powers of 2 between 4 and 64, and must
	be located at multiples of 4. Conversion will fail for coordinates 
	that do not meet these requirements.
	"""
	color_mode = 0
	page_width = 1024 >> color_mode
	suvs = [(int(uvw.u*page_width), int(uvw.v*128)) for uvw in vertuvws]
	
	loc = (min(*[suv[0] for suv in suvs]),
	       min(*[suv[1] for suv in suvs]))
	diffs = [[abs(suvs[i][j] - suvs[(i+1)%3][j]) for i in range(3)]
			 for j in range(2)]
	dim = (max(*diffs[0]), max(*diffs[1]))
	nuvs = tuple([(int((suv[0]-loc[0])/dim[0]), 
			       int((suv[1]-loc[1])/dim[1])) for suv in suvs])
	fw = inv_fw_map[nuvs]
	dim = tuple(int(math.log2(c))-2 for c in dim)
		
	texinfo = WgeoTexinfo()
	texinfo.type = 1
	texinfo.semi_trans = 2
	texinfo.clut_x = 0
	texinfo.clut_y = 0
	texinfo.color_mode = color_mode
	texinfo.region_index = (dim[0] + dim[1]*5 + fw*25)
	texinfo.segment = loc[0] >> (8 - color_mode)
	texinfo.offs_x = (loc[0] >> (3 - color_mode)) & 0x1F
	texinfo.offs_y = loc[1] >> 2
	return texinfo
	
class WorldUnprocessed:
	"""
	Unprocessed form a world which contains a list of polys and a 
	bounding box which encompasses them.
	
	Call process to generate the processed form of the world.
	"""
	count = 0
	def __init__(self, polys):
		self.polys = polys
		self.bound = get_polys_bound(polys)
		self.id = WorldUnprocessed.count
		self.processed = None
		WorldUnprocessed.count += 1
		
	def pickle_fix(self):
		self.polys = [pickle_fix_poly(poly) for poly in self.polys]
		self.bound = pickle_fix_bound(self.bound)
		return self
		
	def process(self):
		if self.processed is not None:
			return self.processed
		
		# preprocess polys
		# - convert poly vert coords to indexed
		# - convert poly texcoords to texinfos/ids 
		polys = []
		verts = []
		idx_map = {}
		for poly in self.polys:
			idxes = []
			for vert in poly.verts:
				key = (vert.x, vert.y, vert.z)
				if key not in idx_map:
					idx_map[key] = len(verts)
					verts.append(vert)
				idx = idx_map[key]
				idxes.append(idx)
			tex = None
			if poly.texid != -1:
				texinfo = uvs_to_texinfo(poly.vertuvws)
				#texid = poly.texid
				texinfo.clut_x = (poly.texid & 0x1F0) >> 4
				texinfo.clut_y = (poly.texid & 0x1FE00) >> 9
				texid = poly.texid & 0xF
				tex = (texid, texinfo)
			polys.append((idxes, tex))
		
		polygons = []
		vertices = []
		texinfos = []
		wgeo = Wgeo(f'a{self.id:03}W')
		for poly in polys:
			idxes, tex = poly
			polygon = WgeoPolygon()
			polygon.a_idx = idxes[0]
			polygon.b_idx = idxes[1]
			polygon.c_idx = idxes[2]
			if tex is not None:
				tpag_idx, texinfo = tex
				polygon.tinf_idx = 1+(len(texinfos)*2)
				polygon.tpag_idx = tpag_idx
				texinfos.append(texinfo)
			polygons.append(polygon)
		for vert in verts:
			vertex = WgeoVertex()
			# vertices are stored relative to the bound location
			rel = vert - self.bound.loc
			rel_z = float_to_fixed(rel.z, 4, 9)
			vertex.x = float_to_fixed(rel.x, 4, 9)
			vertex.y = float_to_fixed(rel.y, 4, 9)
			vertex.z8 = rel_z & 0xFF
			vertex.z2 = (rel_z >> 8) & 3
			vertex.z3 = (rel_z >> 10) & 7
			vertex.r = 255
			vertex.g = 255
			vertex.b = 255
			vertices.append(vertex)
		header = WgeoHeader()
		header.trans_x = float_to_fixed(self.bound.loc.x, 20, 12)
		header.trans_y = float_to_fixed(self.bound.loc.y, 20, 12)
		header.trans_z = float_to_fixed(self.bound.loc.z, 20, 12)
	
		palinfo = WgeoPalinfo()
		palinfo.r = 255
		palinfo.g = 255
		palinfo.b = 255
		palinfo.clut_x = 0
		palinfo.semi_trans = 0
		header.texinfos.append(palinfo)
		header.texinfos.extend(texinfos)
		
		wgeo.header = header
		wgeo.polygons = polygons
		wgeo.vertices = vertices
		self.processed = wgeo
		return wgeo

class SlstUnprocessed:
	"""
	Unprocessed form of an SLST which contains a reference to the 
	processed zone with its parent path and the index of the parent 
	path.
	
	(the processed zone passed is in process of being built; generating 
	the processed slst is the final step in generating the processed 
	zone)
	
	Call process to generate the processed form of the SLST.
	
	(this depends on the processed zone having been populated with 
	 references to the world entries, with zone dimensions, and camera
	 paths; slst delta encodes the sort order of polyons in the worlds 
	 when viewed from each camera path point)
	"""
	count = 0
	def __init__(self, zone, path_idx):
		self.zone = zone
		self.path_idx = path_idx
		self.id = SlstUnprocessed.count
		SlstUnprocessed.count += 1
		
	def process(self):
		# get the zone entry ready to be processed by a c function
		
		# one unfortunate downside to structures in unpacked form is 
		# that they cannot be passed to c code unless they are
		# - packed first OR
		# - appended the variable length section with pointers to the 
		#   cdatas of the unpacked objects
		#
		# we do a combination of the 2
		# 1) pack the zone paths
		# 2) append item pointers to the variable sections of world and
		#    zone entries (sync_cdata takes care of this)
		
		path_idx = self.path_idx
		path = self.zone.paths[path_idx]
		if path.packed == False:
			path.pack()
			self.zone.paths[path_idx] = path # is this needed? 
		for world in self.zone.worlds:
			if world.resolved:
				world.entry = world.entry.sync_cdata()
		self.zone.sync_cdata()
		
		screen_proj = 0x5A
		scene = Scene(screen_proj, self.zone, 1024, 512)
		
		slst = Slst(f'a{self.id:03}S')
		dst = None
		for path_pt_idx, point in enumerate(path.points):
			if path_pt_idx == len(path.points): dst = None
			scene.update_path(path_idx, path_pt_idx)
			scene.compute_visible_polys(1024, 512)
			src = dst
			dst = np.copy(scene.poly_ids)
			if src is None:
				raw = SlstItemRaw()
				raw.poly_ids = dst
				raw.pack()
				slst.items.append(raw)
			else:
				slst.encode(src, dst, path_pt_idx)
		raw = SlstItemRaw()
		raw.poly_ids = dst
		raw.pack()
		slst.items.append(raw)
		path.slst.entry = slst
		return slst
		
def generate_zone_path_slsts(zone, entries):
	for path_idx, path in enumerate(zone.paths):
		print(f"generating slst for {zone.eid} path {path_idx}")
		slst = SlstUnprocessed(zone, path_idx)
		slst = slst.process()
		entries.append(slst)

cur_rot = Angle(0,0,0)

class ZoneUnprocessed:
	"""
	Unprocessed form of a Zone which initially contains 
	n subdivisions of a [section of a] camera path, and a bounding box
	which surrounds the camera path.
	
	Call compute_worlds with a list of unprocessed worlds to compute 
	(and store) the 5 nearest worlds to the zone. 
	Call compute_octree to compute the octree with given resolution
	which approximately encompasses the space occupied by the polygons
	[of worlds] which are contained within the zone.
	
	Then call process to generate the processed form of the zone and 
	all processed entries which it depends on.
	"""	
	count = 0
	def __init__(self, path, res, pad=None):
		self.bound = get_lines_bound(path)
		if pad:
			self.bound = self.calc_bound(self.bound, pad)
		self.paths = split_count(path, res)
		self.octree = None
		self.octree_res = None
		self.worlds = None
		self.inner_polys = None
		self.id = ZoneUnprocessed.count
		ZoneUnprocessed.count += 1
	
	@staticmethod
	def calc_bound(bound, pad):
		
		# we want the path to be located within the center of the bounds
		# and we dont want the bounds to be too narrow or too wide
		dir = bound.p2 - bound.p1
		if abs(dir.x) > abs(dir.z):
			pad = Dimensions(0, pad.h, pad.d)
		else:
			pad = Dimensions(pad.w, pad.h, 0)
		return bound.pad_rect3d(pad)
		
	def pickle_fix(self):
		def pickle_fix_octree(octree):
			for idx, item in enumerate(octree):
				if isinstance(item, list):
					octree[idx] = pickle_fix_octree(item)
				elif item is not None:
					octree[idx] = pickle_fix_bound(item)
			return octree			
		self.bound = pickle_fix_bound(self.bound)
		self.paths = [[pickle_fix_line(line) for line in path] for path in self.paths]
		self.octree = pickle_fix_octree(self.octree)
		self.worlds = [world.pickle_fix() for world in self.worlds]
		self.inner_polys = [pickle_fix_poly(poly) for poly in self.inner_polys]
		return self
		
	def compute_worlds(self, worlds):
		print(f"computing zone {self.id} worlds")
		def dist(world):
			vec = Vector.from_point(self.bound.center - world.bound.center)
			dist = vec.magnitude()
			return dist
		worlds.sort(key=dist)
		self.worlds = worlds[0:5]
		polys = sum([world.polys for world in worlds], [])
		self.inner_polys = get_polys_inside(polys, self.bound)
		
	def compute_octree(self):
		print(f"computing zone {self.id} octree")
		self.octree_res = [6,6,6]
		self.octree = generate_octree(self.inner_polys, self.bound, self.octree_res)
		# self.octree = []
		
	def process(self, entries):
		zone = Zone(f'a{self.id:03}Z')
		print(f"processing zone {self.id} into entry {zone.eid}")
		zone.header = self.generate_zone_header(entries)
		zone.dimensions = self.generate_zone_dimensions()
		zone.paths = self.generate_zone_paths()
		generate_zone_path_slsts(zone, entries)
		self.unresolve_zone(zone)
		return zone
		
	def generate_zone_header(self, entries):
		print(f"generating entry header")
		header = ZoneHeader()
		worlds = [world.process() for world in self.worlds]
		for world in worlds:
			zone_world = ZoneWorld()
			zone_world.eid.entry = world
			header.worlds.append(zone_world)
			if world not in entries:
				entries.append(world)
		
		header.flags = 0x80 # bit 8  - forward/backward zone
		header.game_flags = 3 # bit 1 and bit 2 - 1 = enemies can respawn?
		                      #                   2 = objects can spawn
		                      
		# from n.sanity beach
		header.object_light_matrix[0:] = [61975, 0, 2023,
										  316, 1055, 945,
										  62464, 1019, 63027]
		header.object_back_color[0:] = [1024, 1024, 1024]
		header.object_color_matrix[0:] = [255, 255, 255,
										  255, 255, 255,
										  255, 255, 255]
		header.object_back_color_intensity[0:] = [255, 255, 255]
		header.player_light_matrix[0:] = [61440, 2048, 4096,
										  61973, 2048, 4096, 
										  4096, 63488, 0]
		header.player_back_color[0:] = [614, 614, 614]
		header.player_color_matrix[0:] = [255, 255, 255,
										  255, 255, 255,
										  255, 255, 255]
		header.player_back_color_intensity[0:] = [255, 255, 255]
		
		header.vram_fill_height = 20
		header.vram_fill_r, header.vram_fill_g, header.vram_fill_b = \
			[54, 50, 0]
		header.far_color_r, header.far_color_g, header.far_color_b = \
			[0, 0, 0]
		
		header.death_y = 0 # ?
		header.visiblity_depth = 6144000 # ?????????????
		
		header.paths_idx = 2 # standard start for paths items
		return header
			
	def generate_zone_dimensions(self):
		print("generating zone dimensions")
		
		# def generate_octree_nodes(nodes, offs=0):
			# d = { 'offs': offs + len(nodes)*2 }
			# descs = []
			# def descs_extend(node, d):
				# desc = generate_octree_nodes(node, d['offs'])
				# d['offs'] += len(desc)*2
				# descs.extend(desc)
				# return d['offs'] - len(desc)*2
			# return [-1 if node is None else
					# ((1 << 1) | 1) if not isinstance(node, list) else #solid ground
					# descs_extend(node, d) for node in nodes] + descs
					
		def generate_octree_nodes(nodes, offs=0):
			offs += len(nodes)*2
			parents, descs = [], []
			for node in nodes:
				if node is None:
					parents.append(0)
				elif not isinstance(node, list) or len(node)==1:
					type = 1
					data = ((type << 1) | 1) # solid ground
					parents.append(data)
				else:
					parents.append(offs)
					desc = generate_octree_nodes(node, offs)
					offs += len(desc)*2
					descs.extend(desc)
			return parents + descs

		dimensions = ZoneDimensions()
		
		dimensions.x = float_to_fixed(self.bound.loc.x, 20, 12)
		dimensions.y = float_to_fixed(self.bound.loc.y, 20, 12)
		dimensions.z = float_to_fixed(self.bound.loc.z, 20, 12)
		dimensions.width = float_to_fixed(self.bound.dim.w, 20, 12)
		dimensions.height = float_to_fixed(self.bound.dim.h, 20, 12)
		dimensions.depth = float_to_fixed(self.bound.dim.d, 20, 12)
		
		# the behavior now is to just take the computed octree which
		# bounds the world polygons in the zone at a particular 
		# resolution, convert to packed form, and mark all leaves
		# as solid ground.
		# in the future we should be able to identify pits, walls, ceiling,
		# and at some point when there is UI we should be able to manually
		# mark nodes for other types (miscellaneous death causing)
		collisions = ZoneCollisions()
		nodes_offset = 36 # ffi.offsetof('zone_dimensions', 'collisions') +
		                  # ffi.offsetof('zone_collisions', 'nodes')
		collisions.root = nodes_offset # will always start right after max depths
		collisions.max_depth_x = self.octree_res[0]
		collisions.max_depth_y = self.octree_res[1]
		collisions.max_depth_z = self.octree_res[2]
		collisions.nodes = generate_octree_nodes(self.octree, nodes_offset)
		dimensions.collisions = collisions

		return dimensions
		
	def generate_zone_paths(self):
		global cur_rot
		print("generating zone paths")
		paths = []
		
		for idx, lines in enumerate(self.paths):
			path = ZonePath()
			path.entrance_index = 0
			path.exit_index = 0
			path.cam_mode = 5 # follow player
			path.cam_zoom = 1700 # usual value for n.sanity beach
			
			# TODO: verify scale
			
			direction = lines[-1].points[1] - lines[0].points[0]
			direction = Vector.from_point(direction).normalize()
			#direction = Vector(0,0,-1)
			path.direction_x = float_to_fixed(direction.x, 19, 13) 
			path.direction_y = float_to_fixed(direction.y, 19, 13)
			path.direction_z = float_to_fixed(direction.z, 19, 13)
			path.neighbor_path_count = 0
			
			avg_dist = sum([line.to_vec().vmul(direction).magnitude() 
						for line in lines])/len(lines)
			path.avg_node_dist = float_to_fixed(avg_dist, 20, 12)
			
			# TODO: verify scale
			
			if idx > 0:
				neighbor = ZoneNeighborPath()
				neighbor.goal = 2 # before
				neighbor.relation = 1  
				neighbor.neighbor_zone_idx = 0
				neighbor.path_idx = idx - 1
				path.neighbor_paths.append(neighbor)
			if idx < len(self.paths)-1:
				neighbor = ZoneNeighborPath()
				neighbor.goal = 1 # after
				neighbor.relation = 2 
				neighbor.neighbor_zone_idx = 0
				neighbor.path_idx = idx + 1
				path.neighbor_paths.append(neighbor)
				
			def append_point(line_point, line):
				# note: rot is wrong for the last point in the path
				# it should be determined from the direction between 
				# the last point and the next path's first point 
				point = ZonePathPoint()
				
				dir = line.to_vec()
				#rot = Angle.from_vec(dir)
				rot = Angle(0,atan2(dir.x,dir.z)+math.pi,0)
				point.rot_x = radians_to_ang10(rot.x)
				point.rot_y = radians_to_ang10(rot.y)
				point.rot_z = radians_to_ang10(rot.z)
				
				point.x = float_to_fixed(line_point.x, 20, 12)
				point.y = float_to_fixed(line_point.y, 20, 12)
				point.z = float_to_fixed(line_point.z, 20, 12)
				path.points.append(point)
			
			for line in lines:
				# path points are relative to the zone location
				line_point = line.points[0] - self.bound.loc 
				append_point(line_point, line)
			if line:
				line_point = line.points[1] - self.bound.loc
				append_point(line_point, line)
			paths.append(path)
		return paths
	
	def unresolve_zone(self, zone_entry):
		# we've been storing eids in resolved form (as entry pointers)
		# to interface with c code which cannot do the resolution on its
		# own (an nsd with the page tables does not yet exist)
		
		# after this point we shouldn't need to call any more c code, so
		# we unresolve all eids which have been resolved to pointers 
		# back to eid values
		for world in zone_entry.worlds:
			world.unresolve()
		for path in zone_entry.paths:
			path.slst.unresolve()

class SceneUnprocessed:
	"""
	Unprocessed form of a Scene which initially contains 
	geometry (polys), textures, and a camera rail (lines).
	
	Call compute_worlds to divide the polys into worlds.
	Call compute_zones to divide the camera rail into zones (which will
	also compute the nearest worlds for each).
	Call compute_textures to pack the textures into one or more 256x128 
	texture atlases.
	
	Then call process to generate the processed form of the scene, which
	is a list of representative entries.
	"""
	entity_count = 0
	def __init__(self):
		self.polys = []
		self.lines = []
		self.worlds = []
		self.zones = []
		self.textures = []
		self.spawn = None
	
	def pickle_fix(self):
		self.polys = [pickle_fix_poly(poly) for poly in self.polys]
		self.lines = [pickle_fix_line(line) for line in self.lines]
		self.worlds = [world.pickle_fix() for world in self.worlds]
		self.zones = [zone.pickle_fix() for zone in self.zones]
		# self.textures = [pickle_fix_texture(tex) for tex in self.textures]
		self.spawn = pickle_fix_point(self.spawn)
		
	@staticmethod
	def generate(poly_fn, path_fn, prim_res, prim_size):
		scene = SceneUnprocessed()
		scene.polys = poly_fn(prim_res, prim_size)
		scene.lines = path_fn(prim_res*50, prim_size)
		scene.textures = [] # for now
		return scene
	
	def compute_worlds(self, res):
		print("computing scene worlds")
		poly_groups = partition_polys_group(self.polys, res, True)
		self.worlds = [WorldUnprocessed(polys) for polys in poly_groups]
		
	def compute_zones(self, res, path_res, pad=None):
		print("computing scene zones")
		paths = split_count(self.lines, res)
		for path in paths:
			zone = ZoneUnprocessed(path, path_res, pad)
			self.zones.append(zone)
		for idx, zone in enumerate(self.zones):
			zone.compute_worlds(self.worlds)
			zone.compute_octree()
		
		def flatten(lst):
			items = []
			if isinstance(lst, list):
				for item in lst:
					items.extend(flatten(item))
			else:
				items.append(lst)
			return items
			
		# also compute spawn point
		# choose a random octree node in a random zone
		print("computing scene spawn point")
		# nodes = sum([flatten(zone.octree) for zone in self.zones], [])
		# nodes = [node for node in nodes if node is not None]
		# if len(nodes) == 0:
		#	print("warning: no nodes in octree")
		#node = random.choice(nodes)
		#self.spawn = node.center + Point(0,node.dim.h/2 + 0.5,0)
		self.spawn = self.zones[0].bound.center - self.zones[0].bound.loc
	
	def compute_textures(self):
		# packs individual poly textures into texture pages
		# the old textures are replaced by the new, packed texture pages
		tex_polys = [poly for poly in self.polys if poly.texid != -1]
		if len(tex_polys) == 0:
			return
		
		group = TextureGroup()
		for poly_idx, poly in enumerate(tex_polys):
			texture = self.textures[poly.texid]
			region = Poly(poly.vertuvws)
			dim = Dimensions(32, 32)
			subtexture = texture_region_to_rect(texture, region, dim)
			subtexture = subtexture.convert("I4_ABGR1555")
			subtexture.key = poly_idx
			group.add(subtexture)
			
		dim = Dimensions(256, 128)
		key = lambda idx:idx
		fmt = 'ABGR1555'
		atlas_group = group.to_atlas_group(dim, key, fmt, pack_mode=2, dist_mode=1)
		for poly_idx, poly in enumerate(tex_polys):
			subtexture = atlas_group.get(poly_idx)
			poly.texid = -1
			if subtexture is None:
				continue
			corner_map = {'UL': 0, 'UR': 1, 'LR': 2, 'LL': 3}
			region = Poly(poly.vertuvws)
			winding = get_poly_winding(region)
			uvs = [subtexture.uvs[corner_map[corner]] for corner in winding]
			palette = subtexture.format.palette
			palette_loc = palette.loc + palette.parent.loc
			texid = subtexture.parent.key | \
			        ((int(palette_loc.x) // 16) << 4) | \
			        (int(palette_loc.y) << 9) 
			poly.texid = texid # subtexture.parent.key
			poly.vertuvws = [Texcoord(*uv) for uv in uvs]
		self.textures = atlas_group.to_list()
			
	def process(self):
		print("processing scene")
		entries = []
		for zone in self.zones:
			# this will generate the zdat entry
			# any other entries generated in processing (wgeo,slst) 
			# are appended to the entries list, so we have to append the 
			# additional zone entry
			zone = zone.process(entries)
			entries.append(zone)
		zone_entries = [entry for entry in entries if entry.type == 7]
		self.add_zone_entries_neighbors(zone_entries)
		self.add_zone_entry_entity(zone_entries[0], 0, 0, self.spawn)
		
		tpages = []
		for idx, texture in enumerate(self.textures):
			tpage = TexturePage(f'Lv{idx:02}T')
			eid_value = tpage.eid.value
			tpage['data'] = texture.bytes
			tpage.magic = Page.magic
			tpage.type = 1
			tpage.entry_type = 5
			tpage.eid.value = eid_value
			tpages.append(tpage)
		world_entries = [entry for entry in entries if entry.type == 3]
		self.add_world_entries_tpages(world_entries, tpages)
		
		entries.extend(tpages)
		return entries
	
	def add_world_entries_tpages(self, world_entries, tpages):
		for world in world_entries:
			self.add_world_entry_tpages(world, tpages)
		
	def add_world_entry_tpages(self, world, tpages):
		idxs = {poly.tpag_idx for poly in world.polygons}
		idxs = (list(idxs))[:8]
		idx_map = {idx: i for i, idx in enumerate(idxs)}
		for poly in world.polygons:
			poly.tpag_idx = idx_map.get(poly.tpag_idx, -1)
		for i, idx in enumerate(idxs):
			world.header.tpags.append(tpages[i].eid) # = tpages[i].eid
		
		#for poly in world.polygons:
		#	# undo the textures for now
		#	poly.tinf_idx = 0
		#	poly.tpag_idx = 0
			
		#world.header.tpag_count = len(idxs)
		
	def add_zone_entries_neighbors(self, zone_entries):
		for zone in self.zones:
			neighbors = self.get_neighbors(zone)
			for neighbor in neighbors:
				self.add_zone_entry_neighbor(zone, neighbor, zone_entries)
				
	def add_zone_entry_neighbor(self, zone, neighbor, zone_entries):
		idx = self.zones.index(zone)
		zone_entry = zone_entries[idx]
		neighbor_idx = self.zones.index(neighbor)
		neighbor_entry = zone_entries[neighbor_idx]
		neighbor_idx = len(zone_entry.header.neighbor)
		zone_entry.header.neighbor.append(neighbor_entry.eid)
		if zone == neighbor:
			return
		direction = Vector.from_point(neighbor.bound.center - zone.bound.center)
		direction = direction.normalize()
		neighbor_paths = []
		for path_idx, path in enumerate(zone.paths):
			neighbor_paths = []
			for neighbor_path in neighbor.paths:
				if path[0].points[0] == neighbor_path[-1].points[-1]:
					goal = 2     # 
					relation = 1 # change zone, backward
				elif path[-1].points[-1] == neighbor_path[0].points[0]:
					goal = 1
					relation = 2 # change zone, forward
				else:
					continue
				neighbor_paths.append((neighbor_path, goal, relation))
			for neighbor_path, goal, relation in neighbor_paths:
				neighbor_path_idx = neighbor.paths.index(neighbor_path)
				neighbor_path = ZoneNeighborPath()
				neighbor_path.neighbor_zone_idx = neighbor_idx
				neighbor_path.path_idx = neighbor_path_idx
				neighbor_path.goal = goal
				neighbor_path.relation = relation
				entry_path = zone_entry.paths[path_idx]
				# entry_path.neighbor_paths.append(neighbor_path)
				entry_path.neighbor_paths[entry_path.neighbor_path_count] = neighbor_path
				entry_path.neighbor_path_count += 1
	
	def get_neighbors(self, zone):
		#threshold = 300
		#touching = []
		#nearest = []
		#for neighbor in self.zones:
		#	if zone == neighbor:
		#		continue
		#	collision = zone.bound.find_rect3d_collision(neighbor.bound)
		#	if collision:
		#		touching.append(neighbor)
		#	else:
		#		direction = neighbor.bound.center - zone.bound.center
		#		direction = Vector.from_point(direction)
		#		dist = direction.magnitude()
		#		if dist < threshold:
		#			nearest.append(neighbor)
		#neighbors = ([zone] + (touching + nearest))[:8]
		neighbors = [zone]
		index = self.zones.index(zone)
		if index < len(self.zones)-1:
			neighbors.append(self.zones[index+1])
		if index > 0:
			neighbors.append(self.zones[index-1])
		return neighbors

	def add_zone_entry_entity(self, zone, type, subtype, spawn):
		entity = ZoneEntity()
		entity.type = type
		entity.subtype = subtype
		
		point = ZoneEntityPathPoint()
		point.x = float_to_fixed(spawn.x, 22, 10)
		point.y = float_to_fixed(spawn.y, 22, 10)
		point.z = float_to_fixed(spawn.z, 22, 10)
		entity.path_points.append(point)
		
		entity.init_flags_a = 0
		entity.init_flags_b = 0
		entity.init_flags_c = 0
		
		entity.init_mode_flags = 25
		entity.group = 3 # spawnable; only this group will spawn
		entity.id = SceneUnprocessed.entity_count+1
		SceneUnprocessed.entity_count += 1
		
		zone.entities.append(entity)

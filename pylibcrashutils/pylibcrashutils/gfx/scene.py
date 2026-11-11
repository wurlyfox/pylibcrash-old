import sys
sys.path.append('/home/user/src/pylibcrash')

from libcrash import lib, ffi
from pylibcrash.nsf import Nsf
from pylibcrash.entry import Eid
from pylibcrash.formats.slst import Slst, PolyId
from pylibcrash.formats.wgeo import Wgeo
from pylibcrash.gfx.transform import zdat_project

from pylibcrashutils.gfx.cffi import compute_visible_polys, get_zbuf_image
from pylibcrashutils.gfx.general.geom import Point, Vector, Angle, Poly

from ordered_set import OrderedSet
from copy import copy
import numpy as np

def clamp(a,b,c):
	return min(max(a,b),c)

class Scene:
	"""
	Read-only representation of the crash game scene and its state;
	context within which the world polygons of a zone are projected
	to screen-coordinates.
	
	Consists of the 'state' which includes current zone, current path, 
	and current progress/path point. State in turn affects the camera 
	(trans and rot) as well as the list of visible polygons of current
	zone worlds. Scene holds the list of projected polygons after calls
	to project.
	
	There are functions to:
	 - initialize the state
	 - update the state
	 - update the list of visible polygon(s) [ids] from the current
	   path point slst (occurs automatically with state updates)
	 - project the list of visible polygons to screen coordinates
	 
	There is also a function to directly compute the list of visible 
	polygons given the current state from a software-driven z-buffer 
	check. This can be used along with pylibcrash SLST encoder to create
	SLST items for the zone paths if they do not already exist.
	"""
	def __init__(self, nsf_or_proj, zone, w, h):
		"""
		Constructs a new Scene for the given nsf, zone, and viewport 
		dimensions.
		
		A projection distance may be substituted for the nsf argument.
		This is necessary when the zone is 'under construction' and has 
		not been packed and an nsf/nsd does not yet exist. The zone must
		have one or more worlds and one or more paths (unresolved 
		pointers) for the class to function correctly.
		
		If an nsf is provided then it is assumed that there are existing
		SLSTs, and the deltas_enabled flag is set which enables 
		auto-update of the poly id list upon updating scene state.
		
		:param nsf_or_proj: nsf or projection distance
		:param zone: initial zone
		:param w: viewport width
		:param h: viewport height
		"""
		self.nsf = None
		self.deltas_enabled = False
		self.cam_rot = Angle(0,0,0)
		self.cam_trans = Vector(0,0,0)
		self.screen_offset = Vector(0,0,0)
		self.init_offset(nsf_or_proj, w, h)
		if isinstance(nsf_or_proj, Nsf):
			self.nsf = nsf_or_proj
			self.deltas_enabled = True
		self.init_path(zone, 0, 0)
		
	def init_offset(self, nsf_or_proj, w, h):
		"""
		Initializes the viewport offset vector.
		(used when projecting world to screen coordinates)
		
		A table of values map the projection value (either that 
		specified in the nsd or provided directly) to the actual 
		projection distance, which is used as the z coordinate in the 
		offset vector.
	
		:param nsf_or_proj: nsf or projection distance
		:param w: viewport width
		:param h: viewport height
		"""
		offsets = { 0x1E: 0x3C0,
					0x25: 0x320,
					0x37: 0x1F4,
					0x3C: 0x1CC,
					0x5A: 0x120 }
		if isinstance(nsf_or_proj, Nsf):
			nsf = nsf_or_proj
			ldat = nsf.dir.ldat
			offset_z = offsets[ldat.screen_proj]
		else:
			screen_proj = nsf_or_proj
			offset_z = offsets[screen_proj]
		self.screen_offset.x = int(w / 2)
		self.screen_offset.y = int(h / 2)
		self.screen_offset.z = offset_z
		
	def init_path(self, zone, path_idx, path_pt_idx):
		"""
		Initializes the scene state, including current zone, path index,
		and path point index/progress.
		
		:param zone: initial zone
		:param path_idx: initial path index
		:param path_pt_index: initial path point index
		"""
		self.zone = zone
		self.path_idx = path_idx
		self.path_pt_idx = path_pt_idx
		if self.deltas_enabled:
			self.update_poly_ids(path_idx, path_pt_idx, True)
	
	def update_poly_ids(self, path_idx, path_pt_idx, force=0):
		"""
		Updates the poly id list (i.e. list of ids of visible/to-render 
		polygons) to those visible at the specified path and path point, 
		as encoded by the path SLST. 
		
		Also sets the current path index and path point index.
		
		:param path_idx: path index
		:param path_point_idx: path point index
		:param force: forces reload and re-decode from the nearest 
		              raw/unencoded poly id list 
		"""
		path = self.zone.paths[path_idx]
		slst = self.nsf.entry(path.slst)
		if slst is None:
			self.deltas_enabled = False
			return
		if not path_idx == self.path_idx or force:
			if path_pt_idx < path.length/2:
				raw = slst.items[0]
				self.poly_ids = copy(raw.poly_ids)
				self.path_pt_idx = 0
			else:
				raw = slst.items[-1]
				self.poly_ids = copy(raw.poly_ids)
				self.path_pt_idx = path.length-1
		if path_pt_idx > self.path_pt_idx or force == 'forward':
			for i in range(self.path_pt_idx, path_pt_idx):
				poly_ids = slst.decode_forward(i+1, self.poly_ids)
				self.poly_ids = copy(poly_ids)
		elif path_pt_idx < self.path_pt_idx or force == 'backward':
			for i in range(self.path_pt_idx, path_pt_idx, -1): 
				poly_ids = slst.decode_backward(i, self.poly_ids)
				self.poly_ids = copy(poly_ids)
		self.path_idx = path_idx
		self.path_pt_idx = path_pt_idx
		
	def update_path(self, path_idx, path_pt_idx):
		"""
		Updates the current state (current path and path point).
		
		Index values are clamped to the valid ranges; if a path point 
		index is outside of the valid range it is also interpreted as 
		+1 or -1 path index delta.
		
		The poly id list is also auto-updated if the scene's 
		deltas_enabled flag is set.
		"""
		path = self.zone.paths[path_idx]
		
		path_pt_idx = clamp(path_pt_idx, -1, path.length)
		if path_pt_idx == -1: path_idx -= 1
		elif path_pt_idx == path.length: path_idx += 1
		
		path_count = len(self.zone.paths)
		path_idx = clamp(path_idx, -1, path_count)
		if path_idx == -1:
			path_idx = 0
			path_pt_idx = 0
		elif path_idx == path_count:
			path_idx = path_count - 1
			path_pt_idx = -1
		if path_pt_idx == path.length:
			path_pt_idx = 0
		elif path_pt_idx == -1:
			path = self.zone.paths[path_idx]
			path_pt_idx = path.length - 1
		
		if self.deltas_enabled:
			self.update_poly_ids(path_idx, path_pt_idx)
		self.path_idx = path_idx
		self.path_pt_idx = path_pt_idx
	
	def project(self, normalize=True):
		"""
		Projects visible polygons in the scene (given the current state)
		to screen coordinates.
		"""
		self.polys, self.poly_ids = \
		zdat_project(self.zone, self.path_idx, self.path_pt_idx,
						  self.screen_offset,
						  self.cam_trans, self.cam_rot,
						  normalize = normalize,
						  poly_ids = self.poly_ids,
						  nsf = self.nsf)
			   
	def all_poly_ids(self):
		"""
		Resets the poly id list to all world polys in the current zone.
		"""
		poly_ids = []
		for i, world in enumerate(self.zone.worlds):
			wgeo = world.entry or self.nsf.entry(world)
			if wgeo is None: continue
			for ii, poly in enumerate(wgeo.polygons):
				poly_id = PolyId(i, ii)
				poly_ids.append(poly_id)
		self.poly_ids = np.asarray(poly_ids)
		self.deltas_enabled = False
	
	def sort_polys(self):
		"""
		Sorts the poly id list by average vertex z coordinate.
		"""
		def key_func(p):
			p=p[0]
			z_avg = -sum([v.z for v in p.verts])
			return z_avg
		if len(self.polys) == 0:
			return
		_sorted = list(zip(self.polys, self.poly_ids))
		_sorted.sort(key=key_func)
		self.polys, self.poly_ids = map(np.asarray, zip(*_sorted))
		
	def compute_visible_polys(self, w, h):
		"""
		Recomputes the poly id list using a z-buffer and bounds test of 
		all rasterized world polygons.
		"""
		self.all_poly_ids()
		self.project(normalize=False) # using normalize=False for clipping accuracy
		self.poly_ids, self.polys = \
			compute_visible_polys(self.poly_ids, self.polys, w, h)
		self.sort_polys()
	
	def get_zbuf(self, w, h):
		pixels = get_zbuf_image(w, h, 100)
		return pixels
		
	class PolyPolyId:
		def __init__(self, poly, poly_id):
			self.poly = poly
			self.poly_id = poly_id
			
		def __eq__(self, other):
			if self.poly_id == other.poly_id:
				return True
			return False
			
		def __hash__(self):
			return self.poly_id.__hash__()
			
		def tuple(self):
			return self.poly, self.poly_id
			
	def __sub__(self, other):
		if not self.zone == other.zone:
			return None
		self_polys = map(self.PolyPolyId, self.polys, self.poly_ids)
		other_polys = map(self.PolyPolyId, other.polys, other.poly_ids)
		
		diff = copy(self)
		diff_polys = list(OrderedSet(self_polys) - OrderedSet(other_polys))
		diff_polys = map(self.PolyPolyId.tuple, diff_polys)
		diff.polys, diff.poly_ids = map(np.asarray, zip(*diff_polys))
		diff.deltas_enabled = False
		
		return diff
		
	def __and__(self, other):
		if not self.zone == other.zone:
			return None
			
		self_polys = map(self.PolyPolyId, self.polys, self.poly_ids)
		other_polys = map(self.PolyPolyId, other.polys, other.poly_ids)
		
		sect = copy(self)
		sect_polys = list(OrderedSet(self_polys) & OrderedSet(other_polys))
		sect_polys = map(self.PolyPolyId.tuple, sect_polys)
		sect.polys, sect.poly_ids = map(np.asarray, zip(*sect_polys))
		sect.deltas_enabled = False
		
		return sect

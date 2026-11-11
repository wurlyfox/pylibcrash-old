import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')

import numpy as np

from libcrash import lib, ffi

from pylibcrash.nsd import Nsd
from pylibcrash.nsf import Nsf
from pylibcrash.page import Page, TexturePage
from pylibcrash.entry import Entry, Eid #, Item
from pylibcrash.formats.zdat import Zone

from pylibcrashutils.gfx.general.geom import *


def ns_read(nsf_path):
	"""
	TODO: currently broken; do not use
	Reads an nsf/nsd object pair from the given path.
	
	:return: nsf/nsd pair
	"""
	nsd_path = nsf_path[:-1] + 'D'
	with open(nsf_path, "rb") as nsf_file:
		nsf_data = nsf_file.read()
	with open(nsd_path, "rb") as nsd_file:
		nsd_data = nsd_file.read()
	nsd = Nsd.from_cbytes(nsd_data)
	nsf = Nsf.from_cbytes(nsf_data, nsd)
	
	return nsf, nsd
	
def ns_write(nsf, nsf_path):
	"""
	Writes an nsf/nsd object pair to the given path.
	
	(it is only necessary to specify the nsf object, which already holds 
	 a reference to the nsd)
	"""
	nsd = nsf.dir
	nsd_path = nsf_path[:-1] + 'D'
	with open(nsf_path, "wb") as nsf_file:
		nsf_file.write(nsf.bytes)
	with open(nsd_path, "wb") as nsd_file:
		nsd_file.write(nsd.bytes)
		
def ns_build(lid, entries):
	"""
	Builds an nsf/nsd object pair for the given lid and entries. 
	
	All entries which are essential for game operation are automatically
	included.
	"""
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
		root_dir = "/home/user/src/pylibcrashutils/assets"
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
		path = "/home/user/src/pylibcrashutils/assets/ldat_image.bin"
		with open(path, "rb") as image_file:
			image_data = image_file.read()
		image_buffer = np.frombuffer(image_data, dtype=np.uint8)
		return image_buffer

	entries = get_essential_entries() + entries
	
	# for entry in entries:
		# if entry.type > 20: continue	
		# if not entry.packed: entry.pack()
		# path = f"./output/{str(entry.eid)}.{extension_map[entry.type]}"
		# with open(path, "wb") as entry_file:
			# entry_file.write(entry.bytes)
	
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


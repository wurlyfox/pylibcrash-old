import sys
sys.path.append('/home/user/src/pylibcrash')

from pylibcrash import *
from libcrash import ffi
import numpy as np
from copy import copy

nsd_data = None
nsf_data = None

def ns_import(filename):
	global nsd_data, nsf_data
	nsd_filename = filename[0:-1] + 'D'
	nsf_filename = filename[0:-1] + 'F'
	with open(nsd_filename, "rb") as nsd_file:
		nsd_data = nsd_file.read()
	with open(nsf_filename, "rb") as nsf_file:
		nsf_data = nsf_file.read()
	nsd = Nsd.from_cbytes(nsd_data)
	nsf = Nsf.from_cbytes(nsf_data, nsd)
	# nsf.unpack()
	return nsf, nsd
	
def nsf_entries(nsf):
	entries = {}
	for page in nsf.pages:
		if not page.type == 1:
			for entry in page.entries:
				entries[str(entry.eid)] = entry
	return entries

def nsf_print_page_entries(nsf):
	for page in nsf.pages:
		if not page.type == 1:
			print(f"page {page.pgid}: ")
			for entry in page.entries:
				print(f"entry {entry.eid}: ")
				print(f"item count { len(entry.items) }")
			
def zdat_print_header(zdat):
	header = zdat.header
	
	print("vram_fill_height: ", header.vram_fill_height)
	print("visibility_depth: ", header.visibility_depth)
	vram_fill = [header.vram_fill_r, header.vram_fill_g, header.vram_fill_b]
	far_color = [header.far_color_r, header.far_color_g, header.far_color_b]
	print("vram fill: ", vram_fill)
	print("far_color: ", far_color)
	print("death_y: ", header.death_y)
	#       flags
	print("object_light_matrix: ", header.object_light_matrix)  
	print("object_back_color: ", header.object_back_color) 
	print("object_color_matrix: ", header.object_color_matrix) 
	print("object_back_color_intensity: ", header.object_back_color_intensity) 
	print("player_light_matrix: ", header.player_light_matrix)  
	print("player_back_color: ", header.player_back_color) 
	print("player_color_matrix: ", header.player_color_matrix) 
	print("player_back_color_intensity: ", header.player_back_color_intensity) 
		
	print(zdat.header['tpage_count'])
	for tpage in zdat.header['tpage']:
		print(str(tpage))
	for tchunk in zdat.header.tchunk:
		try:
			page = nsf.page(tchunk)
			for en in page.entries:
				print(str(en.eid))
		except:
			pass

def zdat_print_path_info(zdat):
	print(f"zdat {str(zdat.eid)}")
	for idx, path in enumerate(zdat.paths):
		print(f"path {idx}")
		print(f"cam_mode: {path.cam_mode}")
		print(f"cam_zoom: {path.cam_zoom}")
		print(f"entrance index: {path.entrance_index}")
		print(f"exit index: {path.exit_index}")
		for i, point in enumerate(path.points):
			print(f"point {i}: {point}")

def zdat_print_entities_info(zdat, nsd):
	print(f"zdat {str(zdat.eid)}")
	for idx, entity in enumerate(zdat.entities):
		print(f"entity {idx}")
		print(f"type: {entity.type}, {str(nsd.ldat.exec_map[entity.type])}")
		#print(f"flags: {entity.init_flags_a}, " + \
		#			 f"{entity.init_flags_b},{entity.init_flags_c}")
		print(f"point: {entity.path_points[0]}")
		print(f"init_mode_flags: {entity.init_mode_flags}")
		print(f"id: {entity.id}")
		print(f"group: {entity.group}")
					
def zdat_print_refd_worlds(zdat, nsf):
	print(f"zdat {str(zdat.eid)}")
	print(f"world_count:{zdat.header.world_count}")
	for idx in range(zdat.header.world_count):
		world = zdat.worlds[idx]
		wgeo = nsf.entry(world)
		print(f"world {idx}: {wgeo.eid}")
				   
def gool_print_refd_eids(gool):
	constants = gool.items[2].view(dtype=np.uint32)
	eids = []
	for const in constants:
		eid = Eid()
		eid.value = const
		if str(eid) in entry_dict:
			eids.append(eid)
	print(f"eids referenced by {str(entry.eid)}: {[str(eid) for eid in eids]}")

def nsd_print_exec_map(nsd):
	for idx, eid in enumerate(nsd.ldat.exec_map):
		if eid == Eid.none():
			continue
		print(f"{idx}: {str(eid)}")
	
def ns_print_tpage_ptes(nsf, nsd):
	for pte in nsd.page_table:
		pgid = pte.pgid
		page = nsf.page(pgid)
		if page.type == 1:
			print(f"{str(pte.eid)}: {pte.pgid} is a texture page pte")
	for pte in nsd.page_table:
		pgid = pte.pgid
		page = nsf.page(pgid)
		if page.type == 1:
			tpage = nsd.lookup(pte.eid)
			print(str(tpage.eid))

def ns_validate_page_table(nsf, nsd):
	for pte in nsd.page_table:
		pgid = pte.pgid
		page = nsf.page(pgid)
		if page.type == 1:
			tpage = nsf.entry(pte.eid)
			print(f"{entry.eid} (tpage) found successfully")
		else:
			entry = nsf.entry(pte.eid)
			if entry is None:
				print(f"warning: {pte.eid} not found in pte entry page")
				ns_fix_pte(nsf, nsd, pte)
			else:
				print(f"{entry.eid} found successfully")

def ns_fix_pte(nsf, nsd, pte):
	found_page = None
	eid = pte.eid
	for page in nsf.pages:
		if page.type == 1: continue
		for entry in page.entries:
			if entry.eid == eid:
				found_page = page
				break
		if found_page:
			break
	if found_page:
		print(f"found entry {eid} in page {found_page.pgid}...")
		print("fixing page table entry")
		pte.pgid = found_page.pgid
	else:
		print(f"error: entry {eid} not found in any page!")

def ns_print_page_table(nsd):
	for idx, pte in enumerate(nsd.page_table):
		print(idx, pte.eid, pte.pgid)
		
	for pte in nsd.page_table:
		idx = (pte.eid.value >> 15) & 0xFF
		offset = nsd.ptb_offsets[idx]
		next_offset = 256
		for i in range(idx+1,256):
			if nsd.ptb_offsets[i] != offset:
				next_offset = nsd.ptb_offsets[i]
				break
		rng = nsd.page_table[offset:next_offset]
		print(pte.eid)
		eids = [(pte.eid, pte.pgid) for pte in rng]
		print(eids)
	
def ns_print_page_entry_ptb_offsets(nsf, nsd):
	for page in nsf.pages:
		if page.type == 1: continue
		print(f"page {page.pgid}: ")
		for entry in page.entries:
			eid = entry.eid
			print(f" eid: {eid}, hash: {eid.bucket_hash}")


def ns_fix_entry_order(nsf, nsd):
	# entries packed in pages must be sorted by bucket hash value
	# otherwise page table resolution (from eid->entry) will fail in-game
	# the game does the following to resolve all ptes for entries in 
	# a page:
	#   - calculates the eid hash for the first entry only
	#   - starts at the corresponding pte for the hash and continues 
	#     until the eid for the first entry is found; then replaces with
	#     a pointer to the entry
	#   - continues from -that- position in the page table, searching for
	#     the eid of the second entry, and then replaces upon find, and
	#     so on
	# therefore if the entries are not sorted by index in the page table
	# and consequently by hash value then some search will fail
	
	# this function will fix the order of entries of all such pages with
	# out-of-order entries
	
	
	nsf.unpack()
	nsd.unpack()
	def pte_index(entry):
		pte = nsd.lookup(entry.eid)
		idx = nsd.page_table.index(pte)
		return idx
	for page in nsf.pages:
		if page.type == 1: continue
		page.unpack()
		print(type(page.entries))
		page.entries.sort(key=lambda e: pte_index(e))
	nsd.pack()
	nsf.pack()

	


def main():
	nsf, nsd = ns_import('/home/user/src/pylibcrashutils/nsf/S1/S0000012.NSD')
#	ns_print_tpage_ptes(nsf, nsd)
#	nsd_print_exec_map(nsd)
	
	entries = nsf_entries(nsf)
	for entry in entries.values():
		if entry.type == 7:
			zdat_print_header(entry)
#			zdat_print_path_info(entry)
#			zdat_print_entities_info(entry, nsd)
#			zdat_print_refd_worlds(entry, nsf)
#		if entry.type == 11:
#			gool_print_refd_eids(entry)
	
#	image_data = nsd.ldat.image_data
#	with open("nsd_image.bin", "wb") as image_file:
#		image_file.write(image_data)
	
		
	# ns_validate_page_table(nsf, nsd)
	#for page in nsf.pages:
	#	if page.type == 1: continue
	#	print(page.entry_count)
	#	for entry in page.entries:
	#		print(entry.item_count)
			
	
	#nsd.pack()
	#nsf.pack()
	#ns_print_page_table(nsd)
	#ns_print_page_entry_ptb_offsets(nsf, nsd)
	#ns_fix_entry_order(nsf, nsd)
	#with open("S0000001_.NSD", 'wb') as nsd_file:
	#	nsd_file.write(nsd.bytes)
	#with open("S0000001_.NSF", 'wb') as nsf_file:
	#	nsf_file.write(nsf.bytes)

if __name__ == '__main__':
	main()

import sys
sys.path.append('/home/user/src/pylibcrash')

from pylibcrash import *
from libcrash import ffi
import numpy as np
from datetime import datetime

with open("S0000001.NSD", "rb") as nsd_file:
	nsd_data = nsd_file.read()
with open("S0000001.NSF", "rb") as nsf_file:
	nsf_data = nsf_file.read()

start = datetime.now()
nsd = Nsd.from_cbytes(nsd_data)
nsf = Nsf.from_cbytes(nsf_data, nsd)
elapsed = start - datetime.now()

entry_dict = {}
for page in nsf.pages:
	if not page.type == 1:
		for entry in page.entries:
			entry_dict[str(entry.eid)] = entry


for eid, entry in entry_dict.items():
	if not entry.type == 7: continue
	for i in range(entry.header.world_count):
		world = nsf.entry(entry.header.worlds[i].eid)
		print(world.eid)

	

	
# print(elapsed)
# for entry in entry_dict.values():
	# if entry.type == 11:
		# gool = entry
		# constants = gool.items[2].view(dtype=np.uint32)
		# eids = []
		# for const in constants:
			# eid = Eid()
			# eid.value = const
			# if str(eid) in entry_dict:
				# eids.append(eid)
		# print(f"eids referenced by {str(entry.eid)}: {[str(eid) for eid in eids]}")
		
	#if entry.type == 7:
	#	zone = entry
	#	header = zone.header
		
		
		
		# print("vram_fill_height: ", header.vram_fill_height)
		# print("visibility_depth: ", header.visibility_depth)
		# vram_fill = [header.vram_fill_r, header.vram_fill_g, header.vram_fill_b]
		# far_color = [header.far_color_r, header.far_color_b, header.far_color_b]
		# print("vram fill: ", vram_fill)
		# print("far_color: ", far_color)
		# print("death_y: ", header.death_y)
		
		#       flags
		
		# print("object_light_matrix: ", header.object_light_matrix)  
		# print("object_back_color: ", header.object_back_color) 
		# print("object_color_matrix: ", header.object_color_matrix) 
		# print("object_back_color_intensity: ", header.object_back_color_intensity) 
		# print("player_light_matrix: ", header.player_light_matrix)  
		# print("player_back_color: ", header.player_back_color) 
		# print("player_color_matrix: ", header.player_color_matrix) 
		# print("player_back_color_intensity: ", header.player_back_color_intensity) 
		
		
		# for tpage in zone.header.tpage:
			# print(str(tpage))
		# for tchunk in zone.header.tchunk:
			# try:
				# page = nsf.page(tchunk)
				# for en in page.entries:
					# print(str(en.eid))
			# except:
				# pass
		# break
		
		

# for page in nsf.pages:
	# if not page.type == 1:
		# print(f"page {page.pgid}: ")
		# for entry in page.entries:
			# print(f"entry {entry.eid}: ")
			# print(f"item count { len(entry.items) }")

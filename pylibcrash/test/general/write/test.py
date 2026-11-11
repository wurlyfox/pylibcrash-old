import sys
sys.path.append('/home/user/src/pylibcrash')

from pylibcrash import *
import numpy as np

import random
random.seed()

def byte(value):
	return value.to_bytes(1,byteorder='little')

def mock_entry(eid):
	entry = Entry(eid)
	item_sizes = [(random.randint(8,256) // 4)*4 for _ in range(32)]
	for size in item_sizes:	
		values = [random.randint(0,8) for _ in range(size)]
		item = np.array(values, dtype=np.uint8)
		entry.items.append(item)
	return entry
	
# gc.set_debug(gc.DEBUG_LEAK)
nsd = Nsd()
nsd.ldat = NsdLdat(1)
nsd.ldat.screen_proj = 0x5A
eids = [Eid(f'e{id:03x}R') for id in range(100)]
entries = map(mock_entry, eids)

nsf = Nsf.from_entries(entries, nsd)

nsd.pack()
nsf.pack(nsd)

print(f'summary')
print(f'page count: {len(nsf.pages)}')
for page in nsf.pages:
	print(f'page {page.pgid}')
	print(f'entry count: {len(page.entries)}')
	for entry in page.entries:
		print(f'entry {entry.eid}')
		print(f'item count: {len(entry.items)}')
		for idx, item in enumerate(entry.items):
			print(f'item {idx} length: {len(item)}')

nsf_data = nsf.cbytes
nsd_data = nsd.cbytes

with open("S0000001.NSD", "wb") as nsd_file:
	nsd_file.write(nsd_data)
with open("S0000001.NSF", "wb") as nsf_file:
	nsf_file.write(nsf_data)

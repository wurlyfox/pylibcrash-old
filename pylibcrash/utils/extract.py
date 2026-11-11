import os
import sys
sys.path.append('/home/user/src/pylibcrash')

from pylibcrash import *
import numpy as np

extension_map = {
	1: 'svtx',
	2: 'tgeo',
	3: 'wgeo',
	4: 'slst',
	5: 'tpag',
	6: 'ldat',
	7: 'zdat',
	8: 'cpat',
	9: 'binf',
	10:'opat',
	11:'gool',
	12:'adio',
	13:'midi',
	14:'inst',
	15:'imag',
	16:'link',
	17:'mdat',
	18:'ipal',
	19:'pbak',
	20:'cvtx'
}

def export_nsf(nsf, dir, raw_pages=False, raw_entries=True,
                         page_dirs=True, entry_dirs=False):
	print(f"exporting nsf to {dir}")
	if not os.path.exists(dir):
		os.mkdir(dir)
	for page in nsf.pages:
		if raw_pages:
			export_page(page, dir)
		elif raw_entries:
			export_page_entries(page, dir, page_dirs)
		else:
			export_page_entries_items(page, dir, page_dirs, entry_dirs)
	
def export_page(page, dir):
	bytes = page.bytes
	name = str(page.pgid.value) + '.bin'
	path = dir + '/' + name
	print(f"exporting page {page.pgid} to {path}")
	with open(path, "wb") as page_file:
		page_file.write(bytes.data)
		
def export_page_entries(page, dir, page_dirs=False):
	if page.type == 1:
		export_entry(page, dir, is_tpage=True)
		return
	if page_dirs:
		dir += '/' + str(page.pgid.value)
		if not os.path.exists(dir):
			os.mkdir(dir)
	for entry in page.entries:
		export_entry(entry, dir)
	
def export_page_entries_items(page, dir, page_dirs=False, entry_dirs=False):
	if page.type == 1:
		export_entry(page, dir, is_tpage=True)
		return
	if page_dirs:
		dir += '/' + str(page.pgid.value)
		if not os.path.exists(dir):
			os.mkdir(dir)
	for entry in page.entries:
		export_entry_items(entry, dir, entry_dirs)

def export_entry(entry, dir, is_tpage=False):
	if entry.type is None:
		return
	bytes = entry.bytes
	extension = extension_map[entry.type] if not is_tpage else 'tpag'
	name = str(entry.eid) + '.' + extension
	path = dir + '/' + name
	print(f"exporting entry {str(entry.eid)} to {path}")
	with open(path, "wb") as entry_file:
		entry_file.write(bytes.data)
	
def export_entry_items(entry, dir, entry_dirs=False):
	if entry.type is None:
		return
	if entry_dirs:
		dir += '/' + str(entry.eid)
		if not os.path.exists(dir):
			os.mkdir(dir)
	for idx, item in enumerate(entry.items):
		item_name = str(entry.eid) + '_' + str(idx) + ".bin"
		export_item(item, dir, item_name)
		
def export_item(item, dir, name):
	path = dir + '/' + name
	print(f"exporting item {name} to {path}")
	with open(path, "wb") as item_file:
		item_file.write(item.data)

def print_usage():
	print("usage: nsf_extract.py <nsf filename> [<dest dir>] \
	      [--extract-entries] [--no-page-dirs] [--extract-items] \
	      [--entry-dirs]")
	
def main(args):
	nsf_filename = args[1]
	dest_dir = None
	raw_pages, raw_entries = False, True
	page_dirs, entry_dirs = True, False
	for arg in args[2:]:
		if not arg.startswith("--"):
			dest_dir = arg
		elif arg[2:] == 'extract-entries':
			raw_pages = False
		elif arg[2:] == 'extract-items':
			raw_entries = False
		elif arg[2:] == 'no-page-dirs':
			page_dirs = False
		elif arg[2:] == 'entry-dirs':
			entry_dirs = True
	if dest_dir is None:
		dest_dir = '.'
		
	nsd_filename = nsf_filename[:-1] + 'D'
	with open(nsd_filename, "rb") as nsd_file:
		nsd_data = bytearray(nsd_file.read())
	with open(nsf_filename, "rb") as nsf_file:
		nsf_data = bytearray(nsf_file.read())
		
	nsd = Nsd.from_bytes(nsd_data)
	nsf = Nsf.from_bytes(nsf_data, nsd)
	export_nsf(nsf, dest_dir, 
			   raw_pages, raw_entries, 
			   page_dirs, entry_dirs)
	print("done.")

if __name__ == '__main__':
	args = sys.argv
	if len(args) < 2:
		print_usage()
	else:
		main(args)

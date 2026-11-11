import sys
sys.path.append('/home/user/src/pylibcrash')

from pylibcrash import *
import numpy as np
from PIL import Image

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

def convert_555_to_rgb(data):
	b = ((data & 0x7C00) >> 10) * 8
	g = ((data & 0x3E0) >> 5) * 8
	r = ((data & 0x1F)) * 8
	rgb = [r,g,b]
	return rgb
	
def export_ldat_image(nsd, path):
	
	image_data = nsd.ldat.image_data
	with open("ldat_image.bin", "wb") as bin_file:
		bin_file.write(image_data)
	
	image_data = image_data[0xF8:]
	
	width = 432
	height = 144
	
	palette = image_data.view(dtype=np.uint16)[0:256]
	palette = [convert_555_to_rgb(color) for color in palette]
	image_data = image_data[512:]
	pixels = [palette[idx] for idx in image_data]
		
	array = np.array(pixels, dtype=np.uint8)
	array = np.reshape(array, (height, width, 3))
	
	im = Image.fromarray(array, mode="RGB")
	im.save(path)

def main():
	nsf, nsd = ns_import("S0000009.NSD")
	export_ldat_image(nsd, "./nsd_image_converted.png")

if __name__ == '__main__':
	main()
	

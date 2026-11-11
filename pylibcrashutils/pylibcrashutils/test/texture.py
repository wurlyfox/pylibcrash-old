import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')
import random

import numpy as np

import PIL
from PIL import Image

from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.general.texture import *

def rext(path, ext):
	return path[:path.index('.')] + ext

def open_texture(path):
	"""
	Creates a new Texture from the image file at the specified path.
	
	:param path: image file path
	:return: a new Texture
	"""
	name = path.split('/')[-1]
	image = Image.open(path)
	image = image.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
	pixels = np.frombuffer(image.tobytes(), dtype=np.uint32)
	tdim = Dimensions(image.width, image.height)
	texture = Texture(name, tdim, pixels)
	return texture

def build_atlases(src_dir, dim):
	"""
	Packs all png images from the source directory into one or more 
	atlases of the specified dimensions.
	
	:param src_dir: source directory
	:param dim: atlas dimensions
	:return: an AtlasGroup with the atlases
	"""
	if not os.path.exists(src_dir):
		return None	
	names = os.listdir(src_dir)
	names = [name for name in names if name.endswith(".png")]

	group = TextureGroup()
	for name in names:
		texture = open_texture(src_dir, name)
		group.add(texture)
	atlas_group = group.to_atlas_group(dim, key=lambda idx:f"{idx}.png")
	return atlas_group

def save_atlases(dst_dir, atlas_group):
	"""
	Writes all texture atlases in a group to png images.
	
	:param dst_dir: destination directory
	:param atlas_group: the AtlasGroup
	"""
	
	for key, texture in atlas_group.textures.items():
		texture = texture.convert('ABGR8888')
		dim = texture.dim
		path = f"{dst_dir}/{key}.png"
		res = Image.frombytes("RGBA", (dim.w, dim.h), 
							  texture.data.tobytes())
		res.save(path)

def test_texture_pack_paletted():
	# first test
	atlas_count = 2
	atlas_dim = Dimensions(256, 128)
	texture_dim = Dimensions(32, 32)
	
	# we want just enough textures to fill the total area
	atlas_area = atlas_dim.w*atlas_dim.h
	total_area = atlas_count*atlas_area
	divisor = texture_dim.w*texture_dim.h
	count = int(total_area // divisor)
	
	formats = ['ABGR1555', 'I8_ABGR1555', 'I4_ABGR1555']
	
	group = TextureGroup()
	for tex_type, fmt in enumerate(formats):
		for idx in range(count):
			colors = np.random.randint(256, size=(4,4))
			colors[:,3] = 255
			
			w = int(texture_dim.w * (2**tex_type))
			h = int(texture_dim.h)
			t = (np.arange(w*4).reshape(w,4) // 4) / (w-1)
			x1 = np.tile(colors[1] - colors[0], (w,1))
			x2 = np.tile(colors[3] - colors[2], (w,1))
			rf = np.tile(colors[0], (w,1)) + t*x1
			rl = np.tile(colors[2], (w,1)) + t*x2
			rfr = np.tile(rf.T, h).T.reshape(h,w,4)
			rlr = np.tile(rl.T, h).T.reshape(h,w,4)
			res = rfr*((1-t).repeat(h).reshape(h,w,4)) \
			    + rlr*(t.repeat(h).reshape(h,w,4))
			res = np.array(res, dtype=np.uint8).view(np.uint32).reshape(h,w)
			dim = Dimensions(res.shape[1], res.shape[0])
			texture = Texture(f"tex_{tex_type}_{idx}", dim, res)
			texture = texture.convert(fmt)
			group.add(texture)
	
	atlas_group = TextureGroup()
	groups = group.distribute_using_palettes(atlas_dim, 'ABGR1555', 0.8)
	#groups = group.distribute(atlas_dim)
	
	for idx, group in enumerate(groups):
		atlas = group.pack(atlas_dim, f'atlas_{idx}', fmt='ABGR1555', pack_palettes=True)
		#group.convert('ABGR1555', inplace=True)
		atlas_group.add(atlas)
	
	group2 = TextureGroup()
	atlas_group2 = TextureGroup()
	for key, atlas in atlas_group.textures.items():
		for key, texture in atlas.textures.items():
			tex = texture.convert('ABGR8888')
			group2.add(tex)
	groups2 = group2.distribute(atlas_dim)
	for idx, group in enumerate(groups2):
		atlas = group.pack(atlas_dim, f'atlas_{idx}', fmt='ABGR8888')
		atlas_group2.add(atlas)
				
	dst_dir="/home/user/src/pylibcrashutils/pylibcrashutils/test/texture"
	save_atlases(dst_dir, atlas_group2)
	
def test_texture_pack_paletted_2():
	src_dir = "/home/user/src/genlevel/castle_exterior/"
	
	if not os.path.exists(src_dir):
		return None	
	names = os.listdir(src_dir)
	names = [name for name in names if name.endswith(".png")]

	group = TextureGroup()
	for name in names:
		texture = open_texture(src_dir+'/'+name)
		texture.convert("I4_ABGR1555", inplace=True)
		group.add(texture)
	
	atlas_group = TextureGroup()
	atlas_dim = Dimensions(256, 128)
	groups = group.distribute_using_palettes(atlas_dim, 'ABGR1555', 0.7)
	for idx, group in enumerate(groups):
		atlas = group.pack(atlas_dim, f'castle_atlas_{idx}', fmt='ABGR1555', pack_palettes=True)
		atlas_group.add(atlas)

	group2 = TextureGroup()
	atlas_group2 = TextureGroup()
	for key, atlas in atlas_group.textures.items():
		for key, texture in atlas.textures.items():
			tex = texture.convert('ABGR8888')
			group2.add(tex)
	groups2 = group2.distribute(atlas_dim)
	for idx, group in enumerate(groups2):
		atlas = group.pack(atlas_dim, f'castle_atlas_{idx}', fmt='ABGR8888')
		atlas_group2.add(atlas)
		
	dst_dir="/home/user/src/pylibcrashutils/pylibcrashutils/test/texture"
	save_atlases(dst_dir, atlas_group2)
	
if __name__ == "__main__":
	test_texture_pack_paletted()

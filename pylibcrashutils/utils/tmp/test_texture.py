import os
import sys
sys.path.append('/home/user/src/pylibcrash')
import random

import numpy as np

import PIL
from PIL import Image

from gfx.general.geom import *
from gfx.texture import *
from gfx.formats.wavefront import read_obj, write_obj, WavefrontMaterial

from copy import deepcopy

def rext(path, ext)
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
		path = f"{dst_dir}/{key}"
		res = Image.frombytes("RGBA", (dim.w, dim.h), 
							  texture.data.tobytes())
		res.save(path)

def build_obj_atlases(obj, dim):
	"""
	Transforms and packs the [sub]textures of a waveform obj into one or 
	more atlases of the specified dimensions.
	
	Since atlas subtextures cannot be non-rectangular/non-right-triangular
	and cannot be wrapped/repeated, the transformation will repeat/tile, 
	skew, and scale uv coordinate regions to fit the nearest-in-area 
	right-triangular/rectangular shapes supported by the atlas. 
	
	Texcoords for the obj are modified in-place as well as the material 
	texture [file]names. These [new] filenames are used as the keys of 
	the result atlases and will thus be the names of the corresponding 
	image files if the atlases are written via save_atlases.
	Therefore, if the modified obj is written to a file it will expect 
	the result atlases to be in the same directory.
	
	There is more often than not a loss of quality/distortion which 
	results from the transformation and accompanying change in uvs, 
	particularly for large changes in scale and skew, when the model
	uv regions are non-rectangular/non-right-triangular and/or of 
	dimensions which are non-integer multiples of that of atlas
	subtexture slots. This quality loss may be reduced by partitioning
	polygons at texture wrapping points.
	
	:param obj: waveform object (modified by the function)
	:param dim: atlas dimensions
	:return: an AtlasGroup with the atlases
	"""
	group = TextureGroup()
	for mesh in obj.meshes:
		material = mesh.material
		if material.image_path is None:
			continue
		path = material.image_path
		dir = '/'.join(path.split('/')[:-1])
		name = material.image_name
		texture = open_texture(dir, name)
		poly_uvs = [Poly([Point(*uv) for uv in face.texcoords], [0,0,0])
		            for face in mesh.faces]
		scale = Dimensions(32,32)
		new_textures = [texture_region_to_rect(texture, poly, scale)
						for poly in poly_uvs]
		for idx, texture in enumerate(new_textures):
			texture.key = f"{name}_{idx}" 
			keys.append(texture.key)
			group.add(texture)
	atlas_group = group.to_atlas_group(dim, lambda i: f"atlas_{i}.png")

	idx = 0
	new_materials = []
	for mesh in obj.meshes:
		material_map = {}
		material = mesh.material
		if material.image_path is None:
			new_materials.append(material)
			continue
		for face in mesh.faces:
			key = keys[idx]
			idx += 1
			texture = atlas_group.get(key)
			if texture is None: continue
			uvs = texture.uvs
			
			atlas = texture.parent
			name = atlas.key
			if name not in material_map:
				new_material = WavefrontMaterial.copy(material)
				new_material.name = material.name + \ 
					f"_{len(material_map)+1}"
				new_material.image_name = name
				material_map[name] = new_material
				
			face.texcoords[0][0] = uvs[0].x
			face.texcoords[0][1] = 1.0-uvs[0].y
			face.texcoords[1][0] = uvs[1].x
			face.texcoords[1][1] = 1.0-uvs[1].y
			face.texcoords[2][0] = uvs[3].x
			face.texcoords[2][1] = 1.0-uvs[3].y
			face.material = material_map[name]
		_new_materials = list(material_map.values())
		new_materials.extend(_new_materials)
		if len(_new_materials) > 0:
			mesh.material = _new_materials[0]
	obj.materials = new_materials
	
	return atlas_group
	
src_dir = "/home/user/src/genlevel/castle_exterior"
dst_dir = "/home/user/src/genlevel/"
dim = Dimensions(512,256)

path = src_dir+"/Peaches Castle.obj"
obj = read_obj(path)
atlas_group = build_obj_atlases(obj, dim)
save_atlases(dst_dir, atlas_group)

obj.name = rext(obj.name, '_2.obj')
obj.mtl_name = rext(obj.mtl_name, '_2.mtl')
write_obj(obj)
	

#pygame.init()
#screen = pygame.display.set_mode([dim.w,dim.y])
#img = pygame.image.load(tex_file)

# done = False
# keys = {}
# while not done:
	# for event in pygame.event.get():
		# if event.type == pygame.QUIT:
			# done=True
		# if event.type == pygame.KEYDOWN:
			# keys[event.key] = 1
		# if event.type == pygame.KEYUP:
			# keys[event.key] = 0
	# screen.blit(img, (dim.w, dim.h))
	# pygame.display.flip()
	

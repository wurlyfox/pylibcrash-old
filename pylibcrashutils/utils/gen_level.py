import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')

from PIL import Image

from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.formats.wavefront import *
from pylibcrashutils.gfx.scene_unprocessed import *

from pylibcrashutils.build import ns_build

import pickle

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


def obj_to_scene(obj):
	"""
	Converts a wavefront file to an unprocessed scene.
	
	A 'NurbsPath' object in the source file determines the lines with 
	which to populate the scene.
	
	:param obj: wavefront file object
	:return: the unprocessed Scene
	"""
	# usage: find a wavefront model with the desired scene geometry
	#        then add to the file a path 'NurbsPath' which will act as
	#        the camera path 
	#        (easy to do this in Blender; set projection depth to 
	#        'surface' and draw path over the model; it will be 
    #        projected directly to the surface/'floor' of the model. 
    #        then translate the path upwards in the y-direction to add 
    #        some height offset. [the path can be previewed by creating
    #        a camera and adding a 'follow path' constraint with the 
    #        path as the source object; control the 'offset' parameter
    #        to manually scan/interpolate the current camera location 
    #        through the path, or set play back in animation view to 
    #        auto-move through the path])
    #        then load with load_obj and convert to an unprocessed 
    #        scene with this function
	
	scene = SceneUnprocessed()
	texture_map = {}
	for mesh in obj.meshes:
		for face in mesh.faces:
			verts = [Point(-coord[0], coord[1], -coord[2]) for coord in face.coords]
			vertuvws = [Texcoord(*texcoord) for texcoord in face.texcoords]
			if len(vertuvws) == 0:
				vertuvws = [Texcoord(0,0,1)]*3
			poly = Poly(verts, vertuvws)
			scene.polys.append(poly)
	
	mesh_map = {mesh.name: mesh for mesh in obj.meshes}
	path = mesh_map.get('NurbsPath_NurbsPath.001')
	if path is not None:
		for line in path.lines:
			points = [Point(-coord[0], coord[1]+0, -coord[2]) for coord in line.coords]
			line = Line(points)
			scene.lines.append(line)
	
	polys = (poly for poly in scene.polys)
	for mesh in obj.meshes:
		for face in mesh.faces:
			poly = next(polys)
			if face.material is None or face.material.image_path is None: 
				continue
			
			path = face.material.image_path
			texture = texture_map.get(path)
			if texture is None:
				texture = open_texture(path)
				texture.key = len(texture_map)
				texture_map[path] = texture
				scene.textures.append(texture)
			poly.texid = texture.key
	return scene

def scene_to_ns(scene, lid, dst_dir):
	"""
	Processes an unprocessed scene and writes it to an nsf/nsd file pair.
	"""
	entries = scene.process()
	nsf, nsd = ns_build(lid, entries)
	nsd.pack()
	nsf.pack()
	
	filename = f"S{lid:07X}"
	nsd_path = f"{dst_dir}/{filename}.NSD"
	nsf_path = f"{dst_dir}/{filename}.NSF"
	with open(nsf_path, "wb") as nsf_file:
		nsf_file.write(nsf.bytes)
	with open(nsd_path, "wb") as nsd_file:
		nsd_file.write(nsd.bytes)

def obj_to_ns(src_path, dst_dir=None, dump_scene=False):
	"""
	Converts a wavefront file to a crash level (nsf/nsd file pair).
	
	A 'NurbsPath' object in the source file determines the camera path
	and the positioning of the containing zones. Resolution parameters
	control the level of partitioning of the model and path into 
	sub-units.
	
	Surface collisions are computed from vertex data and a crash 
	spawn point is chosen at random. 
	"""
	if dst_dir is None:
		dst_dir = '/'.join(src_path.split('/')[:-1])

	world_res = [2, 1, 2]
	zone_res = 5
	path_res = 6
	pad = Dimensions(0.4*16, 1.0*4, 0.1*16)
	
	obj = read_obj(src_path)
	scene = obj_to_scene(obj)
	scene.compute_worlds(world_res)
	scene.compute_zones(zone_res, path_res, pad)
	scene.compute_textures()
	if dump_scene:
		with open("scene.pk", "wb") as scene_file:
			pickle.dump(scene, scene_file)
	scene_to_ns(scene, 1, dst_dir)


if __name__ == '__main__':
	build_scene = True
	dump_scene = True
	dir = "/home/user/src/pylibcrashutils/utils/gen_level"
	
	if os.path.exists("scene.pk") and build_scene == False:
		with open("scene.pk", "rb") as scene_file:
			scene = pickle.load(scene_file)
		scene.pickle_fix()
		scene_to_ns(scene, 1, dir)
	else:
		obj_to_ns(f"{dir}/Peaches Castle New.obj", dump_scene=dump_scene)


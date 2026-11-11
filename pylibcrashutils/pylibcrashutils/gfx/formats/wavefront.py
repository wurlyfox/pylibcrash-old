class Wavefront:
	def __init__(self):
		self.name = None
		self.dir = None
		self.mtl_name = None
		self.meshes = []
		self.materials = []
	
	@property
	def path(self):
		return self.dir+'/'+self.name
	
	@path.setter
	def path(self, path):
		name = path.split('/')[-1]
		dir = '/'.join(path.split('/')[:-1])
		self.name = name
		self.dir = dir
		
	@property
	def mtl_path(self):
		return self.dir+'/'+self.mtl_name
	
	@property
	def coords(self):
		return sum([mesh.coords for mesh in self.meshes], [])

	@property
	def texcoords(self):
		return sum([mesh.texcoords for mesh in self.meshes], [])
		
	@property
	def normals(self):
		return sum([mesh.normals for mesh in self.meshes], [])
	
	@property
	def faces(self):
		return sum([mesh.faces for mesh in self.meshes], [])
				
	@property
	def material_map(self):
		return {material.name: material for material in self.materials}

class WavefrontMesh:
	def __init__(self, name, parent):
		self.name = name
		self.parent = parent
		self.coords = []
		self.texcoords = []
		self.normals = []
		self.faces = []
		self.lines = []
		self.material = None
		
	@property
	def verts(self):
		lst = list(zip(self.coords[0::3], 
						self.coords[1::3], 
						self.coords[2::3],
						self.texcoords[0::2],
						self.texcoords[1::2],
						self.normals[0::3],
						self.normals[1::3],
						self.normals[2::3]))
		lst = [list(t) for t in lst]
		return lst
			
class WavefrontMaterial:
	def __init__(self, name, parent):
		self.name = name
		self.parent = parent
		self.Ns = 0.0
		self.Ka = [1.0, 1.0, 1.0]
		self.Kd = [0.64, 0.64, 0.64]
		self.Ks = [0.0, 0.0, 0.0]
		self.Ke = [0.0, 0.0, 0.0]
		self.Ni = 1.0
		self.d = 1.0
		self.illum = 2
		self.image_name = None
		
	@staticmethod
	def copy(other):
		new = WavefrontMaterial(other.name, other.parent)
		new.Ns = other.Ns
		new.Ka = other.Ka
		new.Kd = other.Kd
		new.Ks = other.Ks
		new.Ke = other.Ke
		new.Ni = other.Ni
		new.d = other.d
		new.illum = other.illum
		new.image_name = other.image_name
		return new
		
	@property
	def image_path(self):
		if self.image_name is None:
			return None
		return self.parent.dir+'/'+self.image_name

class WavefrontFace:
	def __init__(self, parent, idxes=None, material=None):
		self.parent = parent
		self.idxes = idxes
		self._material = material
		
		# wavefront = parent.parent
		# self.coords = [wavefront.coords[idx[0]-1] 
					   # if idx[0] is not None else None for idx in idxes]
		# self.texcoords = [wavefront.texcoords[idx[1]-1] 
					   # if idx[1] is not None else None for idx in idxes]
		# self.normals = [wavefront.normals[idx[2]-1] 
		               # if idx[2] is not None else None for idx in idxes]
		
	@property
	def material(self):
		if self._material is None:
			return self.parent.material
		return self._material
		
	@material.setter
	def material(self, material):
		if material == self.parent.material:
			self._material = None
		else:
			self._material = material
	               
	# @property
	# def idxes(self):
		# wavefront = self.parent.parent
		# coords = [wavefront.coords.index(coord)+1
		          # if coord is not None else None 
		          # for coord in self.coords]
		# texcoords = [wavefront.texcoords.index(texcoord)+1 
				     # if texcoord is not None else None 
				     # for texcoord in self.texcoords]
		# normals = [wavefront.normals.index(normal)+1
				   # if normal is not None else None
				   # for normal in self.normals]
		# return list(zip(coords, texcoords, normals))
		
	@property
	def coords(self):
		coord_idxes = [idx[0]-1 for idx in self.idxes]
		pcoords = self.parent.parent.coords
		return sum([[pcoords[idx]] for idx in coord_idxes], [])
	
	@property
	def texcoords(self):
		if any(idx[1] is None for idx in self.idxes):
			return []
		texcoord_idxes = [idx[1]-1 for idx in self.idxes]
		ptexcoords = self.parent.parent.texcoords
		return sum([[ptexcoords[idx]] for idx in texcoord_idxes], [])
	
	@property
	def normals(self):
		if any(idx[2] is None for idx in self.idxes):
			return []
		normal_idxes = [idx[2]-1 for idx in self.idxes]
		pnormals = self.parent.parent.normals
		return sum([[pnormals[idx]] for idx in normal_idxes], [])

class WavefrontLine:
	def __init__(self, parent, idxes=None): #, material=None):
		self.parent = parent
		self.idxes = idxes
		# self._material = material
		
	# @property
	# def material(self):
		# if self._material is None:
			# return self.parent.material
		# return self._material
		
	# @material.setter
	# def material(self, material):
		# if material == self.parent.material:
			# self._material = None
		# else:
			# self._material = material
	               
	# @property
	# def idxes(self):
		# wavefront = self.parent.parent
		# coords = [wavefront.coords.index(coord)+1
		          # if coord is not None else None 
		          # for coord in self.coords]
		# texcoords = [wavefront.texcoords.index(texcoord)+1 
				     # if texcoord is not None else None 
				     # for texcoord in self.texcoords]
		# normals = [wavefront.normals.index(normal)+1
				   # if normal is not None else None
				   # for normal in self.normals]
		# return list(zip(coords, texcoords, normals))
		
	@property
	def coords(self):
		coord_idxes = [idx[0]-1 for idx in self.idxes]
		pcoords = self.parent.parent.coords
		return sum([[pcoords[idx]] for idx in coord_idxes], [])
	
	# @property
	# def texcoords(self):
		# texcoord_idxes = [idx[1]-1 for idx in self.idxes]
		# ptexcoords = self.parent.parent.texcoords
		# return sum([[ptexcoords[idx]] for idx in texcoord_idxes], [])
	
	# @property
	# def normals(self):
		# normal_idxes = [idx[2]-1 for idx in self.idxes]
		# pnormals = self.parent.parent.normals
		# return sum([[pnormals[idx]] for idx in normal_idxes], [])
	
def read_obj(path):
	wavefront = Wavefront()
	wavefront.path = path
	
	with open(path, 'r') as obj_file:
		obj_lines = obj_file.readlines()
	for line in obj_lines:
		if line[-1] == '\n': line = line[:-1]
		parse_obj_line(wavefront, line)
	return wavefront
	
def read_mtl(wavefront, path):
	with open(path, 'r') as mtl_file:
		mtl_lines = mtl_file.readlines()
	for line in mtl_lines:
		if line[-1] == '\n': line = line[:-1]
		parse_mtl_line(wavefront, line)
	return True
	
def write_obj(wavefront, path=None, mtl_name=None):
	def coord_str(val):
		return f"{val[0]} {val[1]} {val[2]}"
	def texcoord_str(val):
		return f"{val[0]} {val[1]}"
	def idx_str(val):
		return str(val) if val is not None else ''
		
	if path is not None:
		wavefront.path = path
	if mtl_name is not None:
		wavefront.mtl_name = mtl_name
	write_mtl(wavefront, wavefront.mtl_path)
	
	lines = []
	lines.append(f"# Blender v2.79 (sub 0) OBJ File: ''")
	lines.append(f"# www.blender.org")
	lines.append(f"mtllib {wavefront.mtl_name}")
	for mesh in wavefront.meshes:
		lines.append(f"o {mesh.name}")
		for coord in mesh.coords:
			lines.append(f"v {coord_str(coord)}")
		for texcoord in mesh.texcoords:
			lines.append(f"vt {texcoord_str(texcoord)}")
		for normal in mesh.normals:
			lines.append(f"vn {coord_str(normal)}")
		#if mesh.material is not None:
		#	lines.append(f"usemtl {mesh.material.name}")
		lines.append(f"s off")
		last_mtl = None
		for face in mesh.faces:
			if face.material != last_mtl:
				lines.append(f"usemtl {face.material.name}")
			last_mtl = face.material
			idxes_str = ' '.join(['/'.join([idx_str(i) for i in idx])
								  for idx in face.idxes])
			lines.append(f"f {idxes_str}")
		for line in mesh.lines:
			# for now only coords for line vertices
			idxes_str = ' '.join(idx_str(idx[0]) for idx in line.idxes)
			lines.append(f"l {idxes_str}")
	with open(wavefront.path, 'w') as obj_file:
		obj_file.writelines([line+'\n' for line in lines])

def write_mtl(wavefront, path):
	def coord_str(val):
		return f"{val[0]} {val[1]} {val[2]}"
		
	lines = []
	materials = wavefront.materials
	lines.append(f"# Blender MTL File: 'None'")
	lines.append(f"# Material Count: {len(materials)}")
	for material in materials:
		lines.append("")
		lines.append(f"newmtl {material.name}")
		lines.append(f"Ns {material.Ns}")
		lines.append(f"Ka {coord_str(material.Ka)}")
		lines.append(f"Kd {coord_str(material.Kd)}")
		lines.append(f"Ks {coord_str(material.Ks)}")
		lines.append(f"Ke {coord_str(material.Ke)}")
		lines.append(f"Ni {material.Ni}")
		lines.append(f"d {material.d}")
		lines.append(f"illum {material.illum}")
		if material.image_name is not None:
			lines.append(f"map_Kd {material.image_name}")
	
	with open(path, 'w') as mtl_file:
		mtl_file.writelines([line+'\n' for line in lines])

def parse_obj_line(wavefront, line):
	args = line.split(' ')
	cmd = args[0]
	# args = args[1:]
	
	material = None
	mesh = wavefront.meshes[-1] if len(wavefront.meshes) > 0 else None
	if cmd == '' or cmd == ' ':
		pass
	elif cmd == '#':
		pass
	elif cmd == 'mtllib':
		name = ' '.join(args[1:])
		wavefront.mtl_name = name
		read_mtl(wavefront, wavefront.mtl_path)
	elif cmd == 'o':
		name = args[1]
		mesh = WavefrontMesh(name, wavefront)
		wavefront.meshes.append(mesh)
	elif cmd == 'v':
		coord = list(float(v) for v in args[1:4])
		mesh.coords.append(coord)
	elif cmd == 'vt':
		texcoord = list(float(v) for v in args[1:3])
		mesh.texcoords.append(texcoord)
	elif cmd == 'vn':
		normal = list(float(v) for v in args[1:4])
		mesh.normals.append(normal)
	elif cmd == 'usemtl':
		name = args[1]
		material = wavefront.material_map[name]
		if mesh.material is None:
			mesh.material = material
	elif cmd == 'f':
		vidxs = args[1:4]
		vidxs = [[int(v) if v != '' else None for v in vidx.split('/')] 
				 for vidx in vidxs]
		face = WavefrontFace(mesh, vidxs)
		if material is not None:
			face.material = material
		mesh.faces.append(face)
	elif cmd == 'l':
		vidxs = args[1:3]
		vidxs = [[int(vidx)] for vidx in vidxs]
		line = WavefrontLine(mesh, vidxs)
		mesh.lines.append(line)
	elif cmd == 's':
		pass
	else:
		raise Exception(f"unsupported command: {cmd}")
	
def parse_mtl_line(wavefront, line):
	args = line.split(' ')
	cmd = args[0]
	# args = args[1:]
	
	material = wavefront.materials[-1] if len(wavefront.materials) > 0 else None
	if cmd == '' or cmd == ' ':
		pass
	elif cmd == '#':
		pass
	elif cmd == 'newmtl':
		name = ' '.join(args[1:])
		material = WavefrontMaterial(name, wavefront)
	elif cmd == 'Ns':
		material.Ns = float(args[1])
	elif cmd == 'Ka':
		material.Ka = list(float(v) for v in args[1:4])
	elif cmd == 'Kd':
		material.Kd = list(float(v) for v in args[1:4])
	elif cmd == 'Ks':
		material.Ks = list(float(v) for v in args[1:4])
	elif cmd == 'Ke':
		material.Ke = list(float(v) for v in args[1:4])
	elif cmd == 'Ni':
		material.Ni = float(args[1])
	elif cmd == 'd':
		material.d = float(args[1])
	elif cmd == 'illum':
		material.illum = int(args[1])
	elif cmd == 'map_Kd':
		material.image_name = ' '.join(args[1:])
	if material is not None and material.name not in wavefront.material_map:
		wavefront.materials.append(material)

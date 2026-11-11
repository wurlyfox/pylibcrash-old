import math
import random

from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.general.list import *


""" ===== bounding box functions ===== """

def get_lines_bound(lines):
	"""
	Gets the bounding box for a list of lines.

	The box spans from a point with the minimum component values amongst
	all line endpoints to a point with the maximum component values.

	:param polys: list of points
	:return: bounding box (Rect3d)
	"""
	xmin = min(min(p.x for p in l.points) for l in lines)
	xmax = max(max(p.x for p in l.points) for l in lines)
	ymin = min(min(p.y for p in l.points) for l in lines)
	ymax = max(max(p.y for p in l.points) for l in lines)
	zmin = min(min(p.z for p in l.points) for l in lines)
	zmax = max(max(p.z for p in l.points) for l in lines)

	loc = Point(xmin, ymin, zmin)
	dim = Dimensions(xmax - xmin, ymax - ymin, zmax - zmin)
	bound = Rect3d(loc, dim)

	return bound

def get_polys_bound(polys):
	"""
	Gets the bounding box for a list of polygons.

	The box spans from a point with the minimum component values amongst
	all polygon vertices to a point with the maximum component values.

	:param polys: list of polygons
	:return: bounding box (Rect3d)
	"""
	xmin = min(min(v.x for v in p.verts) for p in polys)
	xmax = max(max(v.x for v in p.verts) for p in polys)
	ymin = min(min(v.y for v in p.verts) for p in polys)
	ymax = max(max(v.y for v in p.verts) for p in polys)
	zmin = min(min(v.z for v in p.verts) for p in polys)
	zmax = max(max(v.z for v in p.verts) for p in polys)

	loc = Point(xmin, ymin, zmin)
	dim = Dimensions(xmax - xmin, ymax - ymin, zmax - zmin)
	bound = Rect3d(loc, dim)

	return bound


def get_rect2ds_bound(rects):
	"""
	Gets the bounding box for a list of Rect2ds.
	
	The box spans from a point with the minimum component values amongst
	all rect vertices to a point with the maximum component values.

	:param rects: list of rects
	:return: bounding box (Rect2d)
	"""
	xmin = min(rect.p1.x for rect in rects)
	xmax = max(rect.p2.x for rect in rects)
	ymin = min(rect.p1.y for rect in rects)
	ymax = max(rect.p2.y for rect in rects)
	
	loc = Point(xmin, ymin)
	dim = Dimensions(xmax - xmin, ymax - ymin)
	bound = Rect2d(loc, dim)
	
	return bound


def get_lines_bounds(lines, count):
	"""
	Divides a list of lines into count groups and gets the bounding
	boxes for each group.
	
	:param lines: lines
	:param count: number of groups
	:return: list of bounding boxes
	"""
	groups = array_split_count(lines, count)
	bounds = map(get_lines_bound, groups)
	return list(bounds)


def split_rect2d(rect, axes=[1, 1]):
	"""
	Partitions a rect into halves or quadrants

	:param rect: rect to split
	:param axes: list of 0 or 1, indicating whether or not to split by
				 the corresponding axis-aligned segment
	"""
	def rect_idxs(_axes):
		if len(_axes) == 0:
			return [[]]
		_idxs = []
		for i in range(0, int(_axes[-1]) + 1):
			_idxs.extend([nxt+[i] for nxt in rect_idxs(_axes[:-1])])
		return _idxs

	idxs = [Point(idx[0], idx[1]) for idx in rect_idxs(axes)]
	dim = Dimensions(rect.dim.w / (axes[0] + 1),
					 rect.dim.h / (axes[1] + 1))
	rects = [Rect2d(rect.loc + idx.vmul(dim.to_vec()), dim) for idx in idxs]
	return rects
	
def slice_rect2d(rect, mids=[Point(0.5, 0.5)], normalized=True):
	"""
	Slices a rect into 2 or more sub-rects. 
	
	A pair of slices (one aligned with x-axis, one with the y-axis) is 
	performed for each mid-point specified, such that the pair of slices
	intersect at the mid-point. A slice is performed only if the 
	corresponding component is within bounds of and not on the edge of 
	the rect. 
	(i.e. Point(0.5,0) results in only a single [y-axis aligned] slice 
		  of the rect, for the component 0 is on the edge)
	"""
	if normalized:
		mids = [rect.loc + (rect.dim * mid) for mid in mids]
	x_offsets = sorted(list({rect.loc.x} | {mid.x for mid in mids})+[rect.p2.x])
	y_offsets = sorted(list({rect.loc.y} | {mid.y for mid in mids})+[rect.p2.y])
	widths = [x_offsets[i+1]-x_offsets[i] for i in range(len(x_offsets)-1)]
	heights = [y_offsets[i+1]-y_offsets[i] for i in range(len(y_offsets)-1)]
	rects = [Rect2d(Point(x,y),Dimensions(w,h)) 
			 for y,h in zip(y_offsets, heights)
			 for x,w in zip(x_offsets, widths)
			 if w > 0 and h > 0]
	return rects

def slice_rects2d(rects, mids, bound=None):
	"""
	Partitions and slices rects into 2 or more sub-groups.
	"""
	if bound is None:
		bound = get_rect2ds_bound(rects)
	parts = slice_rect2d(bound, mids)
	rects = [[] for _ in len(parts)]
	
	slices = sum([slice_rects2d(rect, mids) for rect in rects], [])
	for slice in slices:
		for idx, part in enumerate(parts):
			if part.find_rect2d_intersection(slice) is not None:
				rects[idx].append(part)
				break
	return res
	
def split_rect3d(rect, axes=[1, 1, 1]):
	"""
	Partitions a rect into halves, quadrants, or octants.

	:param rect: rect to split
	:param axes: list of 0 or 1, indicating whether or not to split by 
				 the corresponding axis-aligned hyperplane
	:return: rect partitions
	"""
	def rect_idxs(_axes):
		if len(_axes) == 0:
			return [[]]
		_idxs = []
		for i in range(0, _axes[0] + 1):
			_idxs.extend([[i] + nxt for nxt in rect_idxs(_axes[1:])])
		return _idxs

	idxs = [Point(idx[0], idx[1], idx[2]) for idx in rect_idxs(axes)]
	dim = Dimensions(rect.dim.w / (axes[0] + 1),
					 rect.dim.h / (axes[1] + 1),
					 rect.dim.d / (axes[2] + 1))
	rects = [Rect3d(rect.loc + idx.vmul(dim.to_vec()), dim) for idx in idxs]
	return rects


def split_rect3d_multi(rect, res):
	"""
	Partitions a rect into halves, quadrants, or octants, and 
	recursively partitions subpartitions at each axis for which the 
	resolution remains non-zero.
	"""
	if res[0] == 0 and res[1] == 0 and res[2] == 0:
		return [rect]
	result = []
	delta = [0 if r == 0 else 1 for r in res]
	rects = split_rect3d(rect, delta)
	res = array_sub(res, delta)
	for rect in rects:
		result.extend(split_rect3d_multi(rect, res))
	return result



def bound_rect_idx(bound, rect):
	"""
	Gets the multi-dimensional index corresponding to 'sub-bound within
	initial bound' in an partition map.

	:param bound: initial bound
	:param rect: sub-bound
	:return: index (list of 3)
	"""
	dim = Dimensions.from_vec(bound.dim.to_vec() // rect.dim.to_vec())
	idx = ((rect.loc - bound.loc) / bound.dim.to_vec()).vmul(dim.to_vec())
	return idx


""" ====== grouping / partitioning functions ====== """

def get_polys_inside(polys, bound):
	polys_filtered = [poly for poly in polys if bound.find_poly_vert_inside(poly)]
	return polys_filtered

def partition_polys_r(polys, res, bound, subpart, partition_map):
	"""
	Recursively splits bound in each axis for which resolution has not 
	been exceeded and while sub-partitions contain polygons, recording 
	the contained polys in partition map when the max resolution is 
	reached.

	:param polys: list of polys to test in the sub-partition
	:param res: remaining resolution
	:param bound: initial boundary of which sub-partition is a division
	:param subpart: sub-partition to split or record contained polys for
	:param partition_map: partition map in which to record polys
	:return: 3d list of subpartitions
	"""
	if res[0] == 0 and res[1] == 0 and res[2] == 0:
		idx = bound_rect_idx(bound, subpart)
		try:
			partition_map[int(idx.x)][int(idx.y)][int(idx.z)] = polys
		except:
			pass
		return
	delta = [0 if r == 0 else 1 for r in res]
	rects = split_rect3d(subpart, delta)
	for rect in rects:
		polys_filtered = [poly for poly in polys 
						  if rect.find_poly_vert_inside(poly)]
		if len(polys_filtered) > 0:
			res_next = sub(res, delta)
			partition_polys_r(polys_filtered, res_next, bound, rect, 
							  partition_map)

def partition_polys(polys, res, linear=False):
	"""
	Partitions polys into subpartitions of shape given by res**2 (or
	res for linear==True).

	:param polys: list of polys to partition
	:param res: 'grid' resolution (log2 for linear=False)
	:param linear: raises res to the power of 2 when False
	:return: 3d list of subpartitions
	"""
	if not isinstance(res, list):
		res = [res, res, res]
	if linear == True:
		lin_res = res
		res = [int(math.ceil(math.log2(r))) for r in res]
		pairs = zip(res, lin_res)
		bound_scale = Vector.from_list([(2 ** r)/l for r, l in pairs])
	else:
		lin_res = [r**2 for r in res]
		bound_scale = Vector(1,1,1)
	partition_map = new_array(lin_res)
	bound = get_polys_bound(polys)
	bound.dim = Dimensions.from_vec(bound.dim.to_vec().vmul(bound_scale))
	partition_polys_r(polys, res, bound, bound, partition_map)
	return partition_map

def partition_polys_group(polys, res, linear=False):
	map = partition_polys(polys, res, linear)
	shape = list_shape(map)
	result = [map[i][j][k] for i in range(shape[0]) 
						   for j in range(shape[1])
						   for k in range(shape[2])]
	return result

"""
Note on the structure of octrees:
	
Leaves are either bounds of space occupied by polys, or None for 
unoccupied space. Any descendants which are children are subdivisions of 
a larger bound (but one which does not exist as a leaf).
"""

def generate_octree_r(polys, bound, res, level=0):
	"""
	Generates an octree of the given resolution from the list of polys. 
	[Do not call this function directly. Call generate_octree.]
	
	This function tests all polys which were previously found to be 
	inside a parent bound for collision with each child bound. Runtime 
	is anywhere from 8**min(res)*len(polys) to 2**max(res)*len(polys)
	
	:param polys: list of polys
	:param bound: bound which contains polys
	:param res: [log2 of the] 'grid' resolution for the octree
	:param level: current level of recursion
	:return: octree of bounds
	"""
	if level > max(res):
		return bound
	axes = [int(level < r) for r in res]
	ret = []
	rects = split_rect3d(bound, axes)
	for rect in rects:
		polys_filtered = [poly for poly in polys 
						  if rect.find_poly_collision(poly)]
		if len(polys_filtered) > 0:
			result = generate_octree_r(polys_filtered, rect, res, level + 1)
		else:
			result = None
		ret.append(result)
	return ret
	
def pixels_3d_to_octree(pixels, bound):
	"""
	Generates an octree from a 3d list of 'pixels'. (Faster alternative 
	to generate_octree_r).
	[Do not call this function directly. Call generate_octree.]
	
	Nonzero pixels are interpreted as solid/occupied space, while values 
	of zero are interpreted as empty/unoccupied space. Altogether the pixel 
	values should be an approximation of the solid parts of space within
	bound. For a given bound, a larger list of pixels will provide a 
	greater resolution.

	It is generally quicker to rasterize a list of polys to a 3d pixel
	list and then use this function to generate an octree, than to call 
	the alternative generate_octree_r.
	
	:param pixels: 3d list of pixels
	:param bound: bound represented by pixels
	:return: octree of bounds
	"""
	def product(*args, repeat=1):
		pools = [tuple(pool) for pool in args] * repeat
		result = [[]]
		for pool in pools:
			result = [x+[y] for x in result for y in pool]
		for prod in result:
			yield tuple(prod)
	shape = list_shape(pixels)
	part = tuple([1 if s == 1 else s // 2 for s in shape])
	times = tuple([1 if s == 1 else 2 for s in shape])
	ranges = product(*[range(time) for time in times]) 
	res = []
	dim = bound.dim / 2
	for rng in ranges:
		offset = Dimensions(*rng)
		loc = bound.loc + dim.vmul(offset)
		sub_bound = Rect3d(loc, dim)
		slices = [(rng[i]*part[i], 
				  (rng[i]+1)*part[i]) for i in range(3)]
		sub = sublist(pixels, slices)
		sub_flat = flatten(sub)
		if all(s == 1 for s in sub_flat):
			res.append(sub_bound)
		elif any(s == 1 for s in sub_flat):
			res.append(pixels_3d_to_octree(sub, sub_bound))
		else:
			res.append(None)
	return res

def generate_octree(polys, bound=None, res=None, mode=1):
	"""
	Generates an octree of the given resolution from the list of polys. 
	
	:param polys: list of polys
	:param bound: bound which contains polys
	:param res: [log2 of the] grid resolution for the octree
	:param mode: algorithm to use to generate octree
	:return: octree of bounds
	"""
	if res is None:
		res = [3,3,3]
	if bound is None:
		bound = get_polys_bound(polys)
	if mode == 0:
		tree = generate_octree_r(polys, bound, res)
	elif mode == 1:
		face_res = [res for res in res]
		pixels = rasterize_3d(polys, bound, res, face_res)
		tree = pixels_3d_to_octree(pixels, bound)
	else:
		raise Exception("invalid generate_octree mode")
	return tree	

def get_poly_winding(poly, ret_type='corner'):
	"""
	Determines the 'winding' for a poly. 
	
	This function defines winding for a poly as the corners of a right 
	triangle which are nearest to the poly vertices, such that the right
	triangle is most 'similar' to the poly (least amount of 
	transformation required to form).

	Note: there is probably a better way of doing this.
	For now winding is determined by:
	- finding a rotation most similar to the original poly which 
	  aligns an edge with an axis
	- concluding that verts on the edge are either 
	  UL, UR; UR, UL; LL, LR; or LR, LL - if aligned with x axis
	  UL, LL; LL, UL; UR, LR; or LR, UR - if aligned with y axis
	- comparing xs or ys of the 2 edge verts to determine the order
	  and then xs or ys of either edge vert and the remaining vert
	  to determine whether upper or lower (for x-aligned),
	  or left or right (for y-aligned)
	- comparing the corresponding component of the remaining vert 
	  against the non-zero component of the midpoint for the 
	  axis-aligned edge verts to determine which of the remaining 2
	  'quadrants' it is in
	
	:param poly: poly
	:param ret_type: [list item] return type. Can be 'corner', 'idxes', 
					 Point, Poly
	:return: list of ret_type, or Poly, describing the winding
	"""
	def point_rotate(vert, ang):
		x = (vert.x*math.cos(ang)-vert.y*math.sin(ang))
		y = (vert.x*math.sin(ang)+vert.y*math.cos(ang))
		return Point(x,y)
	def vector_angle(v1, v2):
		return math.atan2(v2.y, v2.x) - math.atan2(v1.y, v1.x)

	v0, v1, v2 = poly.verts
	edges = [v1-v0, v2-v0, v0-v1, v2-v1, v0-v2, v1-v2]
	angles = sum([[vector_angle(edge, Vector(1,0,0)), 
				   vector_angle(edge, Vector(0,-1,0))] 
				   for edge in edges], [])
	rots = []
	for angle, loc in zip(angles, [v0]*4+[v1]*4+[v2]*4):
		verts = [point_rotate(loc - vert, angle) + loc 
				 for vert in poly.verts]
		verts = [Point(*[round(c, 7) for c in [vert.x,vert.y,vert.z]]) 
				 for vert in verts]
		rot = Poly(verts)
		rots.append(rot)
	
	dists = [sum([(poly.verts[i].x-rot.verts[i].x)**2
	             +(poly.verts[i].y-rot.verts[i].y)**2
	         for i in range(3)]) for rot in rots]
	idx = min(range(len(dists)), key=dists.__getitem__)
	nearest = rots[idx]
	
	# find verts on the same axis
	pairs = [(0,1), (0,2), (1,2)]
	same_x = None
	same_y = None
	for pair in pairs:
		if nearest.verts[pair[0]].x == nearest.verts[pair[1]].x:
			same_x = pair
		if nearest.verts[pair[0]].y == nearest.verts[pair[1]].y:
			same_y = pair
	
	winding=['','','']
	verts = nearest.verts
	xinv = {'L': 'R', 'R': 'L'}
	yinv = {'U': 'L', 'L': 'U'}
	if same_x is not None:
		idxs = [same_x[0], same_x[1], 3-(same_x[0]+same_x[1])]
		va, vb, vc = [verts[idx] for idx in idxs]
		ul = 'U' if va.y < vb.y else 'L'
		lr = 'L' if va.x < vc.x else 'R'
		mid = (va.y + vb.y)/2
		ulc = 'U' if vc.y < mid else 'L'
		winding[idxs[0]] = ul+lr
		winding[idxs[1]] = yinv[ul]+lr
		winding[idxs[2]] = ulc+xinv[lr]
	elif same_y is not None:
		idxs = [same_y[0], same_y[1], 3-(same_y[0]+same_y[1])]
		va, vb, vc = [verts[idx] for idx in idxs]
		lr = 'L' if va.x < vb.x else 'R'
		ul = 'U' if va.y < vc.y else 'L'
		mid = (va.x + vb.x)/2
		lrc = 'L' if vc.x < mid else 'R'
		winding[idxs[0]] = ul+lr
		winding[idxs[1]] = ul+xinv[lr]
		winding[idxs[2]] = yinv[ul]+lrc
	
	point_map = { 'UL': Point(0,0), 
				  'UR': Point(1,0), 
				  'LL': Point(0,1),
				  'LR': Point(1,1) }
	idx_map = { 'UL': 0, 'UR': 1, 'LR': 2, 'LL': 3 }
	if ret_type == Point:
		return [point_map[corner] for corner in winding]
	elif ret_type == Poly:
		return Poly([point_map[corner] for corner in winding])
	elif ret_type == 'idxes':
		return [idx_map[corner] for corner in winding]
	return winding
	
def get_poly_winding2(poly, ret_type='corner'):
	def nearest(point, points):
		dists = [Vector.from_point(point - pa).magnitude() 
				 for pa in points] 
		return min(range(len(dists)), key=dists.__getitem__)
		
	loc = Point(min(vert.x for vert in poly.verts),
				min(vert.y for vert in poly.verts))
	dim = Dimensions(max(vert.x for vert in poly.verts) - loc.x,
	                 max(vert.y for vert in poly.verts) - loc.y)
	bound = Rect2d(loc, dim)
	quad = bound.to_quad()
	
	idxes = [nearest(vert, quad.verts) for vert in poly.verts]
	
	idx_map = {}
	for i, idx in enumerate(idxes):
		if idx not in idx_map:
			idx_map[idx] = []
		idx_map[idx].append(i)
	for idx in idxes:
		if len(idx_map[idx]) > 1:
			va = poly.verts[idx_map[idx][0]]
			vb = poly.verts[idx_map[idx][1]]
			
			da = Vector.from_point(va - quad.verts[idx]).magnitude()
			db = Vector.from_point(vb - quad.verts[idx]).magnitude()
			tv = vb if da < db else va
			ti = 1 if da < db else 0
			dists = [(Vector.from_point(tv - quad.verts[i]).magnitude(), i)
				         for i in range(4) if i != idx]
			midx = min(dists, key=lambda d: d[0])[1]
			idxes[idx_map[idx][ti]] = midx
			break
	
	point_map = { 0: Point(0,0), 
				  1: Point(1,0), 
				  3: Point(0,1),
				  2: Point(1,1) }
	corner_map = { 0: 'UL', 1: 'UR', 2: 'LR', 3: 'LL'}
	if ret_type == Point:
		return [point_map[idx] for idx in idxes]
	elif ret_type == Poly:
		return Poly([point_map[idx] for idx in idxes])
	elif ret_type == 'idxes':
		return idxes
	return [corner_map[idx] for idx in idxes]
	
def get_poly_winding3(poly, ret_type='corner'):
	center = sum(poly.verts, Point(0,0,0)) / 3
	
	winding = [[['UL','UR'],['LL','LR']][int(v.y > center.y)][int(v.x > center.x)]
			   for v in poly.verts]
	
	point_map = { 'UL': Point(0,0), 
				  'UR': Point(1,0), 
				  'LL': Point(0,1),
				  'LR': Point(1,1) }
	idx_map = { 'UL': 0, 'UR': 1, 'LR': 2, 'LL': 3 }
	if ret_type == Point:
		return [point_map[corner] for corner in winding]
	elif ret_type == Poly:
		return Poly([point_map[corner] for corner in winding])
	elif ret_type == 'idxes':
		return [idx_map[corner] for corner in winding]
	return winding
	
""" ====== rasterization functions ====== """
def rasterize_3d(polys, bound=None, res=None, face_res=None):
	"""
	Rasterizes a list of polygons to a 3d list of pixels.
	
	:param polys: list of polys
	:param bound: bound which contains polys
	:param res: [log2 of the] pixel list shape/resolution
	:param face_res: [log2 of the] dimensions for the rasterized area of
					 pixels per polygon plane 
	:return: 3d list of pixels
	"""
	if res is None:
		res = [3,3,3]
	if face_res is None:
		face_res = [3,3]
	if bound is None:
		bound = get_polys_bound(polys)
	res = Dimensions(2**res[0], 2**res[1], 2**res[2])
	face_res = Dimensions(2**face_res[0], 2**face_res[1])

	pixels = new_array((int(res.w), int(res.h), int(res.d)), 0)
	for poly in polys:
		v0, v1, v2 = [((vert - bound.loc) / bound.dim).vmul(res)
					  for vert in poly.verts]
		edges = [v1-v0, v2-v0]
		deltas = [edges[i] / face_res[i] for i in range(2)]
		cur_s, cur = v0.copy(), v0.copy()
		for s in range(int(face_res[0])):
			cur = cur_s
			for t in range(s, int(face_res[1])):
				cur += deltas[0]
				if 0 <= int(cur.x) < int(res.w) and \
				   0 <= int(cur.y) < int(res.h) and \
				   0 <= int(cur.z) < int(res.d):
					pixels[int(cur.x)][int(cur.y)][int(cur.z)] = 1
			cur_s += deltas[1]
	return pixels
	




"""

normally m*a*r

m*face_res


"""
	
"""
2 dimensional version of optimization problem

there is a mesh of adjacent/connected polygons. divide this mesh into groups in the xz
axis such that each group has above a minimum and below a maximum number of polygons and
each group is closest as possible to a square region

1) partition polygons into equal area regions; these regions will be smaller than the 
   groups themselves
2) find the first region that contains polygons

  x x x x x x x x
  x P P P P x x x  (region 1,1)
  x P P x x x x x
  x P P x x x x x
  x P P P x x x x
  x P P P P x x x
  x x x x x x x x

  check in order: (1,0), (0,1), (1,1), (2,0), (0,2), (2,1), (1,2), (2,2), etc. adding
  poly counts until geq to the min; if an entire row or column does not contain polys
  then continue the check only for the columns or rows to the right/below. if the count
  becomes greater than the max, then choose finer grained partitions.

  if we come upon a case where the count is less than the min and no polys are in regions
  to the right or below then the group is a residual group and there is no solution such
  that each group is closest as possible to a square region and has polygon count larger
"""


#
# def partition_polys_r(polys, bound, level):
#     if level > 3:
#         return polys
#     ret = []
#     rects = split_rect3d(bound)
#     for idx, rect in enumerate(rects):
#         polys_filtered = [poly for poly in polys if rect.find_poly_collision(poly)]
#         if len(polys_filtered) > 0:
#             ret.append(partition_polys_r(polys_filtered, rect, level + 1))
#         else:
#             ret.append([])
#     return ret
#
#
# def partition_polys(polys):
#     bound = get_polys_bound(polys)
#     return partition_polys_r(polys, bound, 0)
#
#
# def combine_partitions_r(partitions, level, count_max):
#     if level > 3:
#         return [partitions]
#     combined = []
#     for part in partitions:
#         res = combine_partitions_r(part, level + 1, count_max)
#         for r in res:
#             if len(combined) == 0:
#                 combined.append(r)
#                 continue
#             c_len = len(combined[-1])
#             if c_len + len(r) > count_max:
#                 split = count_max - c_len
#                 combined[-1].extend(r[0:split])
#                 combined.append(r[
#                                 split:])  # issue is that the rect starting the new group  is not necessarily adjacent to the following rects
#             else:
#                 combined[-1].extend(r)
#     return combined
#
#
# def combine_partitions(partitions, count_max):
#     return combine_partitions_r(partitions, 0, count_max)


# def generate_rects_r(polys, bound, level):
	# if level > 3:
		# return [bound]
	# ret = []
	# rects = split_rect3d(bound)
	# for rect in rects:
		# polys_filtered = [poly for poly in polys if rect.find_poly_collision(poly)]
		# if len(polys_filtered) > 0:
			# ret.extend(generate_rects_r(polys_filtered, rect, level + 1))
	# return ret

# def generate_rects(polys, bound=None):
	# if bound is None:
		# bound = get_polys_bound(polys)
	# rects = generate_rects_r(polys, bound, 0)
	# return rects
	
"""

def build_bsp_tree(polys):
	tree = [[],[]]
	polys_bound = get_polys_bound(polys)
	bounds = [get_polys_bound([poly]) for poly in polys]
	poly_bounds = list(zip(polys, bounds))
	
	def split(polys_bound, poly_bounds, axis):
		if len(poly_bounds) == 0:
			return []
		if len(poly_bounds) == 1:
			return poly_bounds[0]
		a, b = [], []
		if axis == 0:
			for poly, bound in poly_bounds:
				if bound.loc.x+bound.dim.w < polys_bound.center.x:
					a.append((poly, bound))
				elif bound.loc.x < polys_bound.center.x:
					a.append((poly, bound))
					b.append((poly, bound))
				if bound.loc.x >= polys_bound.center.x:
					b.append((poly, bound))
			offset = Point(bound.dim.w // 2, 0, 0)
			dim = Dimensions(bound.dim.w // 2, bound.dim.h, bound.dim.d)
		elif axis == 1:
			for poly, bound in poly_bounds:
				if bound.loc.y+bound.dim.h < polys_bound.center.y:
					a.append((poly, bound))
				elif bound.loc.y < polys_bound.center.y:
					a.append((poly, bound))
					b.append((poly, bound))
				if bound.loc.y >= polys_bound.center.y:
					b.append((poly, bound))
			offset = Point(0, bound.dim.h // 2, 0)
			dim = Dimensions(bound.dim.w, bound.dim.h // 2, bound.dim.d)
		elif axis == 2:
			for poly, bound in poly_bounds:
				if bound.loc.z+bound.dim.d < polys_bound.center.z:
					a.append((poly, bound))
				elif bound.loc.z < polys_bound.center.z:
					a.append((poly, bound))
					b.append((poly, bound))
				if bound.loc.z >= polys_bound.center.z:
					b.append((poly, bound))
			offset = Point(0, 0, bound.dim.d // 2)
			dim = Dimensions(bound.dim.w, bound.dim.h, bound.dim.d // 2)
		bound_a = Rect3d(bound.loc,dim)
		bound_b = Rect3d(bound.loc+offset,dim)
		axis = random.choice([0,1,2])
		node = (axis, [split(bound_a, a, axis), split(bound_b, b, axis)])
		return node
		
	axis = random.choice([0,1,2])
	return split(polys_bound, poly_bounds, axis)
"""

from libcrash import lib, ffi
from pylibcrash.formats.slst import PolyId
from pylibcrash.gfx.prim import Poly
from pylibcrash.util import array_to_cptr

from copy import deepcopy
import numpy as np


# use pcsx libs for projection
pcsx = 1

# these buffers will hold the vertex coords and poly ids, respectively,
# for the result polygons.

poly_buf = np.ndarray((4096*2,), dtype=Poly)
poly_id_buf = np.ndarray((4096*2,), dtype=PolyId)

# if gfx data is to be preserved between frames then copy the result
# arrays as the same buffers are used for each call
def zdat_project(zdat, path_idx, path_pt_idx, 
				screen_offset, cam_trans, cam_rot,
				normalize, poly_ids=None, nsf=None):
	global poly_buf, poly_id_buf
	# do this so we aren't restricted on types of the input vector 
	# or their components
	_screen_offset = ffi.new("vec32 *")
	_cam_trans = ffi.new("vec32 *")
	_cam_rot = ffi.new("ang32 *")
	for src, dst in [(screen_offset, _screen_offset), 
	                 (cam_trans, _cam_trans),
	                 (cam_rot, _cam_rot)]:
		dst.x = src.x
		dst.y = src.y
		dst.z = src.z
	poly_count = ffi.new("int *")
	if poly_ids is not None:
		for idx, poly_id in enumerate(poly_ids):
			poly_id_buf[idx] = poly_id
		poly_count[0] = len(poly_ids)
	nsf_cptr = nsf.cptr if nsf is not None else ffi.cast("nsf *", 0)
	lib.zdat_project(nsf_cptr, zdat.cptr, path_idx, path_pt_idx,
					 _screen_offset[0], _cam_trans[0], _cam_rot[0],
					 normalize, pcsx,
					 array_to_cptr(poly_id_buf, "poly_id"), 
					 array_to_cptr(poly_buf, "fpoly"), 
					 poly_count)
	poly_count = poly_count[0]
	polys = deepcopy(poly_buf[0:poly_count])
	poly_ids = deepcopy(poly_id_buf[0:poly_count])
	return polys, poly_ids

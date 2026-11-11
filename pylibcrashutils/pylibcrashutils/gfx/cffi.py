from pylibcrashutils.cffi.libcrashutils import lib, ffi

from pylibcrashutils.gfx.general.geom import Poly
from pylibcrash.formats.slst import PolyId
import numpy as np

pcsx = 1
poly_buf = np.ndarray((8192,), dtype=Poly)
poly_id_buf = np.ndarray((8192,), dtype=PolyId)

def compute_visible_polys(poly_ids, polys, w, h, near=288):
	_poly_ids = ffi.cast("poly_id *", poly_ids.ctypes.data)
	_polys = ffi.cast("fpoly *", polys.ctypes.data)
	_poly_count = ffi.new("int *")
	_poly_count[0] = len(polys)
	lib.compute_visible_polys(_poly_ids, _polys, _poly_count, w, h, 
							  near, pcsx)
	poly_count = _poly_count[0]
	poly_ids = poly_ids[0:poly_count]
	polys = polys[0:poly_count]
	return poly_ids, polys

def clip_polys(poly_ids, polys):
	_dst_poly_ids = ffi.cast("poly_id *", poly_id_buf.ctypes.data)
	_dst_polys = ffi.cast("fpoly *", poly_buf.ctypes.data)
	_poly_ids = ffi.cast("poly_id *", poly_ids.ctypes.data)
	_polys = ffi.cast("fpoly *", polys.ctypes.data)
	_poly_count = ffi.new("int *")
	_poly_count[0] = len(polys)
	lib.clip_polys(_dst_poly_ids, _dst_polys, _poly_ids, _polys,
				   _poly_count)
	poly_count = _poly_count[0]
	dst_polys = poly_buf[0:poly_count]
	dst_poly_ids = poly_id_buf[0:poly_count]
	return dst_poly_ids, dst_polys
	
zbuf_image_buf = np.ndarray((512*1024,), dtype=np.uint32)
def get_zbuf_image(w, h, scale):
	_buf = ffi.cast("uint32_t *", zbuf_image_buf.ctypes.data)
	lib.get_zbuf_image(_buf, w, h, scale, pcsx)
	pixels = zbuf_image_buf[0:w*h]
	return pixels

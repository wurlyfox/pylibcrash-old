import sys
sys.path.append('/home/user/src/ctypemap')
from ctypemap.base import Packable, array_to_cptr

from libcrash import ffi, lib
from pylibcrash.entry import Entry

# from pylibcrash.gfx.prim import PolyId
import numpy as np
from copy import deepcopy

class PolyId(Packable):
	def __init__(self, world_idx=0, poly_idx=0, flag=0):
		self.world_idx = world_idx
		self.poly_idx = poly_idx
		self.flag = flag
	
class SlstDelta(Packable):
	field_map = {
		'data': {
			'count': '$remainder',
			'pack': ('internal', 0)
		}
	}
	
class SlstItem(Packable):
	field_map = {
		'$subclass_id': 'type'
	}
	
class SlstItemRaw(SlstItem):
	subclass_id = 0
	field_map = {
		'$fixed_size': 4, # force a different fixed size
		'poly_ids': {
			'count': 'length',
			'pack': ('internal', 0)
		}
	}
	
class SlstItemDelta(SlstItem):
	subclass_id = 1
	field_map = {
		'delta': {
			'pack': ('internal', 0)
		}
	}

class Slst(Entry):
	subclass_id = 4
	field_map = Entry.extend_field_map()
	field_map['item_data']['type'] = 'slst'
	
	src_buf = None
	dst_buf = None
	@staticmethod
	def _check_bufs():
		# needed because for now can't figure out how to sequence things 
		# so that the dtype for PolyId (and the rest of fixed sized 
		# structs which are set early when calling ctypemap config in 
		# the __init__.py) is generated before the class construction
		if Slst.src_buf == None:
			Slst.src_buf = np.ndarray((4096*2,), dtype=PolyId)
			Slst.dst_buf = np.ndarray((4096*2,), dtype=PolyId)
	
	def decode_forward(self, idx, src):
		Slst._check_bufs()
		if isinstance(self.items[idx], SlstItemRaw):
			raise Exception("can only decode with SlstItemDelta")
		for i in range(len(src)):
			Slst.src_buf[i] = src[i]
		src_len = len(src)
		dst_len = ffi.new("int *")
		callbacks = ffi.cast("slst_callbacks *", 0)
		lib.slst_decode_forward(self.cptr, idx, 
								array_to_cptr(Slst.src_buf), 
								array_to_cptr(Slst.dst_buf),
								src_len, dst_len, callbacks)
		dst = Slst.dst_buf[0:dst_len[0]]
		return dst
		
	def decode_backward(self, idx, src):
		Slst._check_bufs()
		if isinstance(self.items[idx], SlstItemRaw):
			raise Exception("can only decode with SlstItemDelta")
		for i in range(len(src)):
			Slst.src_buf[i] = src[i]
		src_len = len(src)
		dst_len = ffi.new("int *")
		callbacks = ffi.cast("slst_callbacks *", 0)
		lib.slst_decode_backward(self.cptr, idx, 
								array_to_cptr(Slst.src_buf), 
								array_to_cptr(Slst.dst_buf),
								src_len, dst_len, callbacks)
		dst = Slst.dst_buf[0:dst_len[0]]
		return dst
		
	def encode(self, src, dst, idx=None):
		if self.packed == True:
			raise Exception("not supported yet. unpack the Slst first \
			                 to encode")
		src_len = len(src)
		dst_len = len(dst)
		slst_size = ffi.new("size_t *")
		slst_cdata = lib.slst_encode(array_to_cptr(src), array_to_cptr(dst),
							         src_len, dst_len, slst_size)
		if idx is None:
			idx = len(self.items)
		for i in range(len(self.items), idx+1):
			self.items.append(None)
		
		slst = SlstItem.from_cdata(slst_cdata[0], size=slst_size[0])
		self.items[idx] = slst
		return slst

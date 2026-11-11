import pytest

from ctypemap.base import VType
import numpy as np

def example1():
	vtype = VType(2)
	
	vtype.append_to_fixed("f1", np.int32, 0)
	vtype.append_to_fixed("f2", np.float32, 4)
	vtype.append_to_fixed("f3", np.dtype((np.int32, 5)), 8)
	vtype.fixed_size = 28
	
	dt1 = np.dtype((np.int32, 10))
	vtype.append_to_var("f4", dt1, dt1.itemsize, 0)
	vtype.append_to_var("f5", dt1, dt1.itemsize, 1)
	vtype.append_to_var("f6", dt1, dt1.itemsize, 0)
	vtype.append_to_var("f7", dt1, dt1.itemsize, 1)
	
	return vtype
	
def test_vtype_offsets():
	vtype = example1()
	assert vtype.size == 188
	assert vtype.sections[1][0][2] == 28
	assert vtype.sections[1][1][2] == 68
	assert vtype.sections[2][0][2] == 108
	assert vtype.sections[2][1][2] == 148
	
def test_vtype_convert():
	vtype = example1()
	dtype = vtype.dtype
	assert dtype.fields['f1'][1] == 0
	assert dtype.fields['f2'][1] == 4
	assert dtype.fields['f3'][1] == 8
	assert dtype.fields['f4'][1] == 28
	assert dtype.fields['f5'][1] == 108
	assert dtype.fields['f6'][1] == 68
	assert dtype.fields['f7'][1] == 148
	assert dtype.itemsize == 188
	
	

import os
import sys
sys.path.append('/home/user/src/pylibcrash')
sys.path.append('/home/user/src/pylibcrashutils')
import random

import numpy as np

from pylibcrashutils.gfx.general.geom import *
from pylibcrashutils.gfx.general.geom_comp import *


def random_point(size=100):
	coords = tuple([random.randint(-size, size) for _ in range(3)])
	point = Point(*coords)
	return point
	
def random_poly(size=100):
	verts = [random_point(size) for _ in range(3)]
	poly = Poly(verts)
	return poly
			
def test_bsptree():
	poly_count = 20
	polys = [random_poly() for _ in range(poly_count)]
	
	tree = build_bsp_tree(polys)
	
	print(tree)
	
if __name__ == '__main__':
	test_bsptree()
	

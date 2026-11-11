def float_to_fixed(value, int_blen, frac_blen, signed=True):
	blen = int_blen + frac_blen
	sign = False
	if signed and value < 0:
		blen -= 1
		value = -value
		sign = True
	mask = (1 << blen) - 1
	factor = (1 << (frac_blen-1))
	value = (int(value*factor) & mask)
	if sign:
		value = -value
	return value
	
def fixed_to_float(value, frac_blen):
	factor = (1 << (frac_blen))
	value = value / factor
	return value

import math
def radians_to_ang10(value):
	# map range 0-2pi to 0-1024 => mult by 1024/2pi
	return int(value*2048/math.pi)
	
def ang10_to_radians(value):
	return value*(math.pi/2048)
	

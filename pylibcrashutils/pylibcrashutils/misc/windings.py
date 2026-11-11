import numpy as np

def idx2d(array, val):
	shape = array.shape
	for y in range(shape[0]):
		for x in range(shape[1]):
			if array[y,x] == val:
				return (y,x)
	return None
	
def genperms(vals):
	def valid_perm(perm):
		grid = gengrid(perm)
		flatgrid = grid.ravel().tolist()
		return len([c for c in flatgrid if c != ' ']) == len(vals)
	offsets = [-1,0,1]
	offsets = [(x,y) 
			   for x in offsets for y in offsets 
			   if x != 0 or y != 0]
	nextperms = [[]]
	if len(vals) > 2:
		nextperms = genperms([vals[0]] + vals[2:]) + genperms(vals[1:])
	perms = [[(vals[0], vals[1], x, y)] + nextperm 
			 for nextperm in nextperms for x,y in offsets]
	perms = [perm for perm in perms if valid_perm(perm)]
	return perms
	
def gengrid(perm, grid=None):
	desc = perm[0]
	v1, v2, x, y = desc
	if grid is None:
		grid = np.array([[v1]])
	grid = np.pad(grid, 1, constant_values=[' '])
	idx = idx2d(grid, v1)
	idx = (idx[0]+y, idx[1]+x)
	grid[idx] = v2
	if len(perm) > 1:
		grid = gengrid(perm[1:], grid)
	return grid

def gridstr(grid):
	return '\n'.join([''.join(row) for row in grid.tolist()])

def descstr(desc):
	ops = ['>', '==', '<']
	v1, v2, x, y = desc
	str = f'{v1}.x {ops[x+1]} {v2}.x, {v1}.y {ops[y+1]} {v2}.y'
	return str
	
def permstr(perm):
	return '\n'.join(descstr(desc) for desc in perm)

def infostr(perm, vals):
	idxmap = {(0,1): 0, (0,2): 1,
	          (1,0): 0, (1,2): 1,
	          (2,0): 0, (2,1): 1}
	valmats = [[0,0,0,0] for _ in range(3)]
	for desc in perm:
		i1 = vals.index(desc[0])
		i2 = vals.index(desc[1])
		idx1, idx2 = i1, idxmap[(i1,i2)]
		valmats[idx1][idx2] = desc[2]
		valmats[idx1][idx2+2] = desc[3]
	
	infos = []
	for val, mat in zip(vals, valmats):
		if (mat[0] == mat[3] == 1) or (mat[1] == mat[2] == 1):
			str = 'UL'
		elif (mat[0] == 1 and mat[3] == -1) or (mat[1] == 1 and mat[2] == -1):
			str = 'UR'
		elif (mat[0] == -1 and mat[3] == 1) or (mat[1] == -1 and mat[2] == 1):
			str = 'LL'
		elif (mat[0] == mat[3] == -1) or (mat[1] == mat[2] == -1):
			str = 'LR'
		else:
			str = 'UNK'
		infos.append(f'{val}: {str}')
	return '\n'.join(infos) 

		
perms = genperms(['a', 'b', 'c'])
for perm in perms:
	grid = gengrid(perm)
	print(gridstr(grid))
	print(permstr(perm))
	print(infostr(perm, ['a','b','c']))

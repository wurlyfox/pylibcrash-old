import math
from copy import copy

def new_array(dims, fill_val=None):
    if len(dims) == 0:
        return fill_val
    arr = [new_array(dims[1:]) for i in range(0, dims[0])]
    return arr


def array_add(a, b):
    res = copy(a)
    for idx, val in enumerate(a):
        res[idx] += b[idx]
    return res


def array_sub(a, b):
    res = copy(a)
    for idx, val in enumerate(a):
        res[idx] -= b[idx]
    return res


def array_mul(a, b):
    res = copy(a)
    for idx, val in enumerate(a):
        res[idx] *= b[idx]
    return res


def array_split_idxs(arr, idxs):
    res = []
    prev_idx = idxs[0]
    for idx in idxs[1:]:
        res.append(arr[prev_idx:idx])
        prev_idx = idx
    res.append(arr[prev_idx:])
    return res


# array of length m, divide into n groups, size of n-1 will be floor(m/n)
# size of last will be floor(m/n) + m%n
# size s_i can be made closer to the last size by

# s_i = floor(m/n) + 1
# s_n = floor(m/n) + m%n - p   (for p x i's)


def array_split_count(arr, group_count):
    group_size = len(arr) // group_count
    
    idxs = [group_size * i for i in range(0, group_count)]
    return array_split_idxs(arr, idxs)


def array_split_size(arr, group_size, ceil=True):
    if ceil: group_count = int(math.ceil(len(arr) / group_size))
    else: group_count = len(arr) // group_size
    idxs = [group_size * i for i in range(0, group_count)]
    return array_split_idxs(arr, idxs)

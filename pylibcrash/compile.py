import pathlib
import cffi

headers = ["types.h", 
           "entry.h", "misc/suffix_tree.h", "page.h", 
           "nsd.h", "nsf.h", 
           "gfx.h",
           "entry/slst.h", "entry/wgeo.h", "entry/zdat.h",
           "misc/slst_stats.h"]

def ffi_read_headers(base_path):
    for path in pathlib.Path.iterdir(base_path):
        if path.is_dir():
            ffi_read_headers(path)
        elif path.suffix == '.h':
            with open(path) as h_file:
                ffi.cdef(h_file.read())

ffi = cffi.FFI()
base = pathlib.Path('./include')
for path in headers:
    path_str = str(base / path)
    with open(path_str) as h_file:
        ffi.cdef(h_file.read())

ffi.cdef('\nvoid *malloc(size_t size);\nvoid free(void *ptr);\n')

source = '\n'.join(
    ['#include "include/' + header + '"' for header in headers]
)

ffi.set_source(
    "libcrash",
    source,
    libraries=[":libcrash.so"],
    library_dirs=["/usr/lib/"],
    extra_link_args=["-Wl,-I./include/"]
)
ffi.compile()

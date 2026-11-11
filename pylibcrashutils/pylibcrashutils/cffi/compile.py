import pathlib
import cffi

headers = ["gfx.h", "rasterize.h", "soft.h"]

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
    "libcrashutils",
    source,
    libraries=[":libcrashutils.so"],
    library_dirs=["/usr/lib/"],
    extra_link_args=["-Wl,-I./include/"]
)
ffi.compile()

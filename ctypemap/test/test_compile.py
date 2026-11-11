from cffi import FFI
ffibuilder = FFI()

struct_defs = """
typedef struct {
  int32_t count;
  uint32_t items[];
} test_struct_a;

typedef struct {
  int32_t count;
  union {
    uint32_t offsets[0];
    uint8_t *items[0];
  };
} test_struct_b;

typedef struct {
  int32_t count;
  union {
    uint32_t offsets[0];
    test_struct_b *structs[0];
  };
} test_struct_c;

typedef struct {
  int32_t count;
  union {
    uint32_t offsets[0];
    test_struct_b *structs[0];
  };
} test_struct_d;

typedef struct {
  uint32_t dummy;
  test_struct_b structs[];
} tsb_array;

typedef struct {
  int32_t count;
  union {
    uint32_t offsets[64];
    uint8_t *items[64];
  };
  uint8_t item_data[];
} test_struct_e;

"""

ffibuilder.cdef("""
typedef unsigned char uint8_t;
typedef signed int int32_t;
typedef unsigned int uint32_t;
""" + struct_defs)
ffibuilder.set_source("_test", source=struct_defs)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)

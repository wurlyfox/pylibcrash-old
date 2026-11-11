# crashlib Makefile

# sources
SRC = src/nsd.c \
      src/nsf.c \
      src/page.c \
      src/entry.c \
      src/entry/slst.c \
      src/gfx/sin.c \
      src/gfx/transform.c \
      src/gfx/rasterize.c \
      src/gfx/pcsx/gte.c \
      src/misc/suffix_tree.c \
      src/misc/slst_stats.c \
      

OBJ = $(SRC:.c=.o)
OUT = bin/libcrash.so

# include dirs.
INCLUDE = -I./include/ -I./src/gfx/pcsx

# C compiler flags (-g -O3 -Wall)
CCFLAGS = -fPIC -g -w -O3

# compiler
CC = gcc

all: $(SRC) $(OUT)

clean:
	rm -r $(OBJ) $(OUT)
	
install:
	sudo cp bin/libcrash.so /usr/lib

.c.o:
	$(CC) $(INCLUDE) -c $< -o $@ $(CCFLAGS)
	
$(OUT): $(OBJ)
	$(CC) $(OBJ) -shared -o $(OUT) $(CCFLAGS)

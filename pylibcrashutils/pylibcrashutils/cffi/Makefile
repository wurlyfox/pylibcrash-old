# libcrashutils Makefile

# sources
SRC = src/gfx/gfx.c \
      src/gfx/rasterize.c \
      src/gfx/pcsx/soft.c \

OBJ = $(SRC:.c=.o)
OUT = bin/libcrashutils.so

# include dirs.
## INCLUDE = -I./include/

# C compiler flags (-g -O3 -Wall)
CCFLAGS = -fPIC -g -w -O3

# compiler
CC = gcc

all: $(SRC) $(OUT)

clean:
	rm -r $(OBJ) $(OUT)
	
install:
	sudo cp bin/libcrashutils.so /usr/lib

.c.o:
	$(CC) $(INCLUDE) -c $< -o $@ $(CCFLAGS)
	
$(OUT): $(OBJ)
	$(CC) $(OBJ) -shared -o $(OUT) $(CCFLAGS)

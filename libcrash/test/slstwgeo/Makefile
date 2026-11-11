# crashlib test Makefile

# sources
SRC = main.c scene.c rasterize.c shader.c stats.c
            
OBJ = $(SRC:.c=.o)
OUT = test

# include dirs.
INCLUDE = -I../../include/

# C compiler flags (-g -O3 -Wall)
CCFLAGS = -L /usr/lib/ -l:libcrash.so -lSDL -g -w

# compiler
CC = gcc

all: $(SRC) $(OUT)

.c.o:
	$(CC) $(INCLUDE) -c $< -o $@ $(CCFLAGS)

$(OUT): $(OBJ)
	$(CC) $(OBJ) -o $(OUT) $(CCFLAGS)

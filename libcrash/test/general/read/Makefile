# crashlib test Makefile

# sources
SRC = main.c
            
OBJ = $(SRC:.c=.o)
OUT = test

# include dirs.
INCLUDE = -I../../../include/

# C compiler flags (-g -O3 -Wall)
CCFLAGS = -L /usr/lib/i386-linux-gnu -l:libcrash.so -g -w -m32

# compiler
CC = gcc

all: $(SRC) $(OUT)

.c.o:
	$(CC) $(INCLUDE) -c $< -o $@ $(CCFLAGS)

$(OUT): $(OBJ)
	$(CC) $(OBJ) -o $(OUT) $(CCFLAGS)

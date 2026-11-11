# crashlib test Makefile

# sources
SRC = main.c
            
OBJ = $(SRC:.c=.o)
OUT = test

# include dirs.
INCLUDE = -I../../include/

# C compiler flags (-g -O3 -Wall)
CCFLAGS = -L../../bin/ -l:libcrash.so -g -w

# compiler
CC = gcc

all: $(SRC) $(OUT)

.c.o:
	$(CC) $(INCLUDE) $(CCFLAGS) -c $< -o $@
  
$(OUT): $(OBJ)
	$(CC) $(CCFLAGS) $(OBJ) -o $(OUT)

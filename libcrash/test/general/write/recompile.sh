#!/bin/bash
cd ~/src/libcrash
make clean
make
make install
cd ~/src/libcrash/test/general/write
rm *.o
rm test
make
gdb test

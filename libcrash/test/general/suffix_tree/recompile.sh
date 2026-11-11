#!/bin/bash
cd ~/src/libcrash
make clean
make
make install
cd ~/src/libcrash/test/general/suffix_tree
rm *.o
rm test
make
gdb test

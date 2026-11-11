#!/bin/bash
cd ~/src/libcrash
make clean
make
make install
cd ~/src/libcrash/test/wgeo
rm main.o
rm test
make
gdb test

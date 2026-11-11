cp ~/src/SCUS_949.00 ./PSX.EXE
mkdir game
cd game
mkdir S0
cd ..
cp ./PSX.EXE ./game
cp ./{S0000001.NSD,S0000001.NSF} ./game/S0
mkisofs -o ./game.iso ./game
iso2psx game.iso game.bin
cp game.bin ~/src/pcsx-hdbg
cd ~/src/pcsx-hdbg
./pcsx-hdbg gamefile=./game.bin region=ntsc bootlevel=1


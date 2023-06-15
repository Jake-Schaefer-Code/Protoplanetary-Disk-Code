#!/bin/bash

# first arg: new folder name
# second arg: sheet name
cd models
mkdir "$1"
python3 paramWriter.py "$1"
mv modParametersNEW.dat "/home/driscollg/models/$1/parameters.dat"
cd "$1"
~/torus/bin/torus.openmp parameters.dat > output.txt
cd ~
cd models
python3 csvWriter.py $1 $1


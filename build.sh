#!/bin/bash
source ~/miniconda/etc/profile.d/conda.sh
conda activate factoriotwitchbot
rm -rf ./distribution
mkdir distribution
cd ./distribution
pyinstaller ../run.py --name "FactorioTwitchBot" --onefile --icon ../icon.ico
cp ../settings.txt ./dist/settings.txt
cp ../README.md ./dist/README.txt
cp -r ../configs ./dist/configs

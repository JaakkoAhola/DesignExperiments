#!/bin/bash
unzip data/01_source/*.zip
mv ECLAIR-SOURCE-DATA/* data/01_source/
mv description_of_variables.pdf data/01_source/
rm -rf ECLAIR-SOURCE-DATA/

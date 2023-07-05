#!/bin/bash
mkdir -p data/01_source 
mkdir -p data/02_raw_output data/02_raw_output/design_stats_maxpro data/02_raw_output/design_stats_maximin

mkdir -p data/03_figure_analysis
mkdir -p batch_job_scripts/logs/R batch_job_scripts/logs/bsp


echo "REPO=${PWD}" | tee .env src_python/.env src_r/.env

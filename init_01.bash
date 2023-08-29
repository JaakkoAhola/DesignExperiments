#!/bin/bash
mkdir -p data/01_source 
mkdir -p data/02_raw_output data/02_raw_output/design_stats_maxpro data/02_raw_output/design_stats_maximin

mkdir -p data/03_figure_analysis
mkdir -p batch_job_scripts/logs/R batch_job_scripts/logs/bsp batch_job_scripts/logs/filldistance

if [[ $( hostname ) == "puhti"* ]]; then
	PUHTIPYTHON="PYTHONUSERBASE=/projappl/project_2000360/project_pip_packages_python-data_3.8-22.10"
else
	PUHTIPYTHON=""
fi

cat > .env << EOF
REPO=${PWD}
FIGEXTENSION=.pdf
${PUHTIPYTHON}
EOF
for i in src_python/.env src_r/.env
do
	ln -s ${PWD}/.env ${PWD}/${i}
done

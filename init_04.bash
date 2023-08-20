#!/bin/bash
for i in $(cat .env); do export $i; done


if [[ -z $REPO ]]
then echo "REPO env missing" && exit 1
fi

arr=(SBnight SBday SALSAnight SALSAday)
for i in "${arr[@]}";
do echo $i;
MAXMIN_FOLDER=${REPO}/data/02_raw_output/design_stats_maximin/${i}/manuscript
MAXPRO_FOLDER=${REPO}/data/02_raw_output/design_stats_maxpro/${i}/manuscript
mkdir -p ${MAXMIN_FOLDER} ${MAXPRO_FOLDER}
FILE=${REPO}/data/01_source/manuscript_designs/${i}.csv
DESIGN_POINTS=$(wc -l ${FILE}  | awk '{print $1 - 1}')
ln -sf ${FILE} ${MAXMIN_FOLDER}/manuscript_${DESIGN_POINTS}.csv
ln -sf ${FILE} ${MAXPRO_FOLDER}/manuscript_${DESIGN_POINTS}.csv
done

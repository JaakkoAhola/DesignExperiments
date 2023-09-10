#!/bin/bash
module load python-data/3.8-22.10
for i in $(cat ../.env)
do
  export $i
done

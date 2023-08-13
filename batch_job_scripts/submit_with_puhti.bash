#!/bin/bash
module load python-data/3.8-22.10
export PYTHONUSERBASE=/projappl/project_2000360/project_pip_packages_python-data_3.8-22.10

python submit_job.py $1
for i in $(ls temp_*.bash);
   do sbatch $i
      sleep 5s
      echo "Removing file $i"
      rm $i
done

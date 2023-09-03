#!/bin/bash
#SBATCH --job-name=LookUP
#SBATCH --account=project_2000360
#SBATCH --time=72:00:00
#SBATCH --mem-per-cpu=12G
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=END #uncomment to enable mail
#SBATCH --mail-user=jjahol@utu.fi
#SBATCH --output=logs/duplicates_test_lookup_table_%j.log

module load python-data/3.8-22.10
echo "module loaded"

export PYTHONUSERBASE=/projappl/project_2000360/project_pip_packages_python-data_3.8-22.10
cd ../src_python
srun python test_sample_set_for_duplicates.py

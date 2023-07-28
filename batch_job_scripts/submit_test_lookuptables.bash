#!/bin/bash
#SBATCH --job-name=LookUP
#SBATCH --account=project_2000360
#SBATCH --time=72:00:00
#SBATCH --mem-per-cpu=10G
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mail-type=END #uncomment to enable mail
#SBATCH --mail-user=jjahol@utu.fi
#SBATCH --output=logs/lookuptable_%j.log

module load python-data/3.8-22.10
echo "module loaded"

export PYTHONUSERBASE=/projappl/project_2000360/project_pip_packages_python-data_3.8-22.10
cd ../src_python
srun python test_lookup_table.py

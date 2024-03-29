#!/bin/bash
#SBATCH --job-name=PURE
#SBATCH --account=project_2000360
#SBATCH --time=72:00:00
#SBATCH --mem-per-cpu=12G
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mail-type=END #uncomment to enable mail
#SBATCH --mail-user=jjahol@utu.fi
#SBATCH --output=PURE_%j.log

source ${HOME}/init.login.sh
source ${HOME}/init.aliases.sh


module load python-data/3.8-22.10

cd ../src_python
srun python test_source_for_constraints.py

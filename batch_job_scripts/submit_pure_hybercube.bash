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

module load python-data/3.8-22.10

cd ../src_python
srun python run_hypercube_source_constraints_met.py

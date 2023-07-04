#!/bin/bash
#SBATCH --job-name=FillD_4N
#SBATCH --account=project_2000360
#SBATCH --time=01:30:00
#SBATCH --mem-per-cpu=850M
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mail-type=END #uncomment to enable mail
#SBATCH --mail-user=jaakko.ahola@virnex.fi
#SBATCH --output=logs/FillDistance_4N_maximin_%j.log


source ${HOME}/init.login.sh
source ${HOME}/init.aliases.sh

module purge
module load python-data/3.8-22.10

srun python ${KOODIT}/DesignExperiments/FillDistance.py /scratch/project_2000360/Dissertation_results/Design/FillDistance/fill_distance_LVL4Night_maxmin.yaml

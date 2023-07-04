#!/bin/bash
#SBATCH --job-name=BSP_4N_0
#SBATCH --account=project_2000360
#SBATCH --time=00:20:00
#SBATCH --mem-per-cpu=2500M
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mail-type=END #uncomment to enable mail
#SBATCH --mail-user=jaakko.ahola@virnex.fi
#SBATCH --output=logs/bsp/SALSAnight_bsp_0_v2_%j.log

source ${HOME}/init.login.sh
source ${HOME}/init.aliases.sh

echo "initialised"
module load python-data/3.8-22.10 #python-data/3.7.3-1
echo "module loaded"
srun python ${KOODIT}/DesignExperiments/BinarySpacePartition.py 2 0

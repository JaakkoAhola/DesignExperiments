#!/bin/bash
#SBATCH --job-name=BSP_3N_0
#SBATCH --account=project_2000360
#SBATCH --time=00:01:00
#SBATCH --mem-per-cpu=5G
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mail-type=END #uncomment to enable mail
#SBATCH --mail-user=jaakko.ahola@virnex.fi
#SBATCH --output=logs/bsp/SBnight_testi.log

source ${HOME}/init.login.sh
source ${HOME}/init.aliases.sh
echo "initialised"

module load python-data/3.8-22.10
echo "module loaded"

cd ${KOODIT}/DesignExperiments/src_python python run_bsp.py

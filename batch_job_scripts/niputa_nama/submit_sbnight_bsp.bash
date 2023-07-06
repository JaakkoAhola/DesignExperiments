#!/bin/bash
#SBATCH --job-name=BSP_3N_0
#SBATCH --account=project_2000360
#SBATCH --time=00:20:00
#SBATCH --mem-per-cpu=2500M
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mail-type=END #uncomment to enable mail
#SBATCH --mail-user=jjahol@utu.fi
#SBATCH --output=logs/bsp/SBnight_bsp_0_%j.log

module load python-data/3.8-22.10
echo "module loaded"

cd ../src_python
srun python run_bsp.py 0 0

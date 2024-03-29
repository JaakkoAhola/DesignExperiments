#!/bin/bash
#SBATCH --job-name=BSP_3N_0
#SBATCH --account=project_2000360
#SBATCH --time=00:01:00
#SBATCH --mem-per-cpu=2500M
#SBATCH --partition=test
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mail-type=END #uncomment to enable mail
#SBATCH --mail-user=jjahol@utu.fi
#SBATCH --output=logs/bsp/SBnight_testi.log

module load python-data/3.8-22.10
echo "module loaded"

export PYTHONUSERBASE=/projappl/project_2000360/project_pip_packages_python-data_3.8-22.10
cd ../src_python
srun python run_bsp.py

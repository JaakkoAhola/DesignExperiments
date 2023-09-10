#!/bin/bash
#SBATCH --job-name=FIG_FILL
#SBATCH --account=project_2000360
#SBATCH --time=00:29:00
#SBATCH --mem-per-cpu=4G
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=END
#SBATCH --mail-user=jjahol@utu.fi
#SBATCH --output=logs/analyse_figure_filldistance_%j.log

module load python-data/3.8-22.10
echo "module loaded"

export PYTHONUSERBASE=/projappl/project_2000360/project_pip_packages_python-data_3.8-22.10
cd ../src_python
srun python analyse_figure_filldistance.py

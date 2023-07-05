#!/bin/bash
#SBATCH --job-name=R_test
#SBATCH --account=project_2000360
#SBATCH --time=00:15:00
#SBATCH --mem-per-cpu=10G
#SBATCH --partition=test
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mail-type=ALL #uncomment to enable mail
#SBATCH --mail-user=jjahol@utu.fi
#SBATCH --output=logs/R/test_R_%j.log

# Load r-env
module load r-env/430

# Clean up .Renviron file in home directory
if test -f ~/.Renviron; then
    sed -i '/TMPDIR/d' ~/.Renviron
fi

# Specify a temp folder path
echo "TMPDIR=/scratch/project_2000360" >> ~/.Renviron

# change directory
cd ../src_r/
# Run the R script
srun apptainer_wrapper exec Rscript --no-save run_comined_eclair.R 1

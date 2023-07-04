#!/bin/bash
#SBATCH --job-name=R_4D
#SBATCH --account=project_2000360
#SBATCH --time=72:00:00
#SBATCH --mem-per-cpu=10G
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mail-type=END #uncomment to enable mail
#SBATCH --mail-user=jaakko.ahola@virnex.fi
#SBATCH --output=logs/R/SALSAday_R_%j.log


source ${HOME}/init.login.sh
source ${HOME}/init.aliases.sh

# Load r-env-singularity
module load r-env-singularity/3.6.3

# Clean up .Renviron file in home directory
if test -f ~/.Renviron; then
    sed -i '/TMPDIR/d' ~/.Renviron
fi

# Specify a temp folder path
echo "TMPDIR=/scratch/<project>" >> ~/.Renviron

# Run the R script
srun singularity_wrapper exec Rscript --no-save ${KOODIT}/DesignExperiments/comined_eclair.R 5

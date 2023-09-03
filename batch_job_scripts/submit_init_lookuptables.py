#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 28.7.2023
@licence: MIT licence Copyright
"""

import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import yaml
import subprocess


def get_var_code(variable):

    dictio = {'q_inv': 'q_inv',
              'tpot_inv': 't_inv',
              'lwp': 'lwp',
              'tpot_pbl': 't',
              'pbl': 'pbl',
              'cdnc': 'cdnc',
              'ks': 'ks',
              'as': 'as',
              'cs': 'cs',
              'rdry_AS_eff': 'reff',
              'cos_mu': 'cos'}

    return dictio[variable]


def get_batch_job_script(variable):

    var = get_var_code(variable)

    jobname = f"LU_{var}"

    email = "jjahol@utu.fi"

    account = "project_2000360"

    walltime = "72:00:00"

    memory = "10G"

    logfile = f"logs/lookuptable_{var}_%j.log"

    batch_job_script = f"""#!/bin/bash
#SBATCH --job-name={jobname}
#SBATCH --account={account}
#SBATCH --time={walltime}
#SBATCH --mem-per-cpu={memory}
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=END
#SBATCH --mail-user={email}
#SBATCH --output={logfile}

module load python-data/3.8-22.10
echo "module loaded"

export PYTHONUSERBASE=/projappl/project_2000360/project_pip_packages_python-data_3.8-22.10
cd ../src_python
srun python init_lookup_table.py {variable}
"""

    return batch_job_script


def submit_job(variable):
    batch_job_script = get_batch_job_script(variable)
    print()
    print(variable)
    print(batch_job_script)
    with open(f"temp_submit_init_lookuptable_{variable}.bash", "w") as file:
        file.write(batch_job_script)


def main():
    load_dotenv()

    temp_list = sys.argv[1:]
    if len(temp_list) > 0:
        variable_list = temp_list
    else:
        variable_list = ["q_inv", "tpot_inv", "lwp", "tpot_pbl",
                         "pbl", "cdnc", "ks", "as", "cs", "rdry_AS_eff", "cos_mu"]
    print(variable_list)
    for variable in variable_list:
        submit_job(variable)


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {(end - start):.2f} seconds.")

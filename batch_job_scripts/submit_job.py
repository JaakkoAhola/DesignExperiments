#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 6.7.2023
@licence: MIT licence Copyright
"""

import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import yaml
import subprocess


def readYAML(path):
    with open(path, "r") as stream:
        try:
            output = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return output


def validate_input_yaml(parameter_dict):
    assert parameter_dict["runtype"] in ["bsp", "filldistance", "R"]
    assert parameter_dict["setname"] in ["sbnight", "sbday", "salsanight", "salsaday"]
    assert parameter_dict["measure"] in ["maximin", "maxpro"]
    assert isinstance(parameter_dict["reps"], int)
    assert isinstance(parameter_dict["designpoints"], int)


def get_runtypecode(runtype):

    runtypecode_dict = {"R": "R",
                        "filldistance": "FD",
                        "bsp": "BSP"}

    return runtypecode_dict[runtype]


def get_setnamecode(setname):

    setnamecode_dict = {"sbnight": "sbn",
                        "sbday": "sbd",
                        "salsanight": "san",
                        "salsaday": "sad"
                        }

    return setnamecode_dict[setname]


def get_measurecode(measure):

    measurecode_dict = {"maximin": "MA",
                        "maxpro": "MP"}

    return measurecode_dict[measure]


def get_jobname(parameter_dict):
    runtypecode = get_runtypecode(parameter_dict["runtype"])

    setnamecode = get_setnamecode(parameter_dict["setname"])

    measurecode = get_measurecode(parameter_dict["measure"])

    jobname = f"{runtypecode}{setnamecode}{measurecode}"

    return jobname


def get_walltime(runtype):

    walltime_dict = {"bsp": "00:20:00",
                     "filldistance": "01:30:00",
                     "R": "72:00:00"}

    return walltime_dict[runtype]


def get_memory(runtype):

    memory_dict = {"bsp": "3250M",
                   "filldistance": "850M",
                   "R": "10G"}
    return memory_dict[runtype]


def get_logfile(parameter_dict):

    runtype = parameter_dict["runtype"]
    setname = parameter_dict["setname"]
    measure = parameter_dict["measure"]

    return f"logs/{runtype}/{runtype}_{setname}_{measure}_%j.log"


def get_command(runtype):

    command_dict = {"R": "srun apptainer_wrapper exec Rscript --no-save run_comined_eclair.R",
                    "filldistance": "srun python run_fill_distance.py",
                    "bsp": "srun python run_bsp.py"}

    return command_dict[runtype]


def get_argument(parameter_dict):

    runtype = parameter_dict["runtype"]
    setname = parameter_dict["setname"]
    measure = parameter_dict["measure"]
    designpoints = parameter_dict["designpoints"]
    reps = parameter_dict["reps"]

    if runtype == "R":
        setint_dict = {'test': 1,
                       'sbnight': 2,
                       'sbday': 3,
                       'salsanight': 4,
                       'salsaday': 5}

        setint = setint_dict[setname]

        measureint_dict = {"maximin": 0, "maxpro": 1}

        measureint = measureint_dict[measure]

    elif runtype == "filldistance":

        argument = f"../input_yaml/filldistance/{runtype}_{setname}_{measure}.yaml"

    elif runtype == "bsp":
        setint_dict = {'sbnight': 0,
                       'sbday': 1,
                       'salsanight': 2,
                       'salsaday': 3}
        setint = setint_dict[setname]

        measureint_dict = {"maximin": 0, "maxpro": 1}

        measureint = measureint_dict[measure]

    if runtype in ["bsp", "R"]:
        argument = f"{setint} {measureint} {designpoints} {reps}"

    return argument


def get_module_and_setup(parameter_dict):

    runtype = parameter_dict["runtype"]
    account = parameter_dict["account"]

    if runtype == "R":
        module_and_setup = f"""# Load r-env
module load r-env/430

# Clean up .Renviron file in home directory
if test -f ~/.Renviron; then
    sed -i '/TMPDIR/d' ~/.Renviron
fi

# Specify a temp folder path
echo "TMPDIR=/scratch/{account}" >> ~/.Renviron

# change directory
cd ../src_r/
"""
    elif runtype in ["bsp", "filldistance"]:
        module_and_setup = """# load python
module load python-data/3.8-22.10
export PYTHONUSERBASE=/projappl/project_2000360/project_pip_packages_python-data_3.8-22.10
echo "module loaded"

cd ../src_python
"""

    return module_and_setup


def get_batch_job_script(parameter_dict):

    jobname = get_jobname(parameter_dict)

    email = parameter_dict["email"]

    account = parameter_dict["account"]

    walltime = get_walltime(parameter_dict["runtype"])

    memory = get_memory(parameter_dict["runtype"])

    logfile = get_logfile(parameter_dict)

    module_and_setup = get_module_and_setup(parameter_dict)

    command = get_command(parameter_dict["runtype"])

    argument = get_argument(parameter_dict)

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

{module_and_setup}
{command} {argument}
"""

    return batch_job_script


def submit_job(parameter_dict):
    batch_job_script = get_batch_job_script(parameter_dict)

    print(batch_job_script)

    runtype = parameter_dict["runtype"]
    setname = parameter_dict["setname"]
    measure = parameter_dict["measure"]
    designpoints = parameter_dict["designpoints"]
    reps = parameter_dict["reps"]

    filename = f"temp_submit_{runtype}_{setname}_{measure}_{designpoints}_{reps}.bash"
    with open(filename, "w") as file:
        file.write(batch_job_script)


def main():
    load_dotenv()
    try:
        parameterFile = sys.argv[1]
        parameter_dict = readYAML(parameterFile)

        runtype_list = parameter_dict["runtype"]
        setname_list = parameter_dict["setname"]
        measure_list = parameter_dict["measure"]
        design_points_list = parameter_dict["designpoints"]

        reps = parameter_dict["reps"]
        account = parameter_dict["account"]
        email = parameter_dict["email"]
    except IndexError:
        runtype_list = ["bsp", "R", "filldistance"]
        setname_list = ["sbnight", "sbday", "salsanight", "salsaday"]
        measure_list = ["maximin", "maxpro"]
        account = "project_2000360"
        email = "jjahol@utu.fi"

    for runtype in runtype_list:
        for setname in setname_list:
            for measure in measure_list:
                for design_point in design_points_list:

                    submit_dict = {"runtype": runtype,
                                   "setname": setname,
                                   "measure": measure,
                                   "account": account,
                                   "designpoints": design_point,
                                   "reps": reps,
                                   "email": email}
                    print(submit_dict)

                    validate_input_yaml(submit_dict)
                    submit_job(submit_dict)


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {(end - start):.2f} seconds.")

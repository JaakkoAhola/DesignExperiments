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

    memory_dict = {"bsp": "2500M",
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

    if runtype == "R":
        setint_dict = {'test': 1,
                       'sbnight': 2,
                       'sbday': 3,
                       'salsanight': 4,
                       'salsaday': 5}

        setint = setint_dict[setname]

        measureint_dict = {"maximin": 0, "maxpro": 1}

        measureint = measureint_dict[measure]

        argument = f"{setint} {measureint}"

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

        argument = f"{setint} {measureint}"

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

    batch_job_script = f"""
#!/bin/bash
# SBATCH --job-name={jobname}
# SBATCH --account={account}
# SBATCH --time={walltime}
# SBATCH --mem-per-cpu={memory}
# SBATCH --partition=small
# SBATCH --nodes=1
# SBATCH --ntasks=1
# SBATCH --mail-type=END
# SBATCH --mail-user={email}
# SBATCH --output={logfile}

{module_and_setup}
{command} {argument}
"""

    return batch_job_script


def submit_job(parameter_dict):
    batch_job_script = get_batch_job_script(parameter_dict)

    runtype = parameter_dict["runtype"]
    setname = parameter_dict["setname"]
    measure = parameter_dict["measure"]

    with open(f"temp_submit_{runtype}_{setname}_{measure}.bash", "w") as file:
        file.write(batch_job_script)
        subprocess.call(["sbatch", batch_job_script])
        subprocess.call(["rm", batch_job_script])


def main():
    load_dotenv()
    try:
        parameterFile = sys.argv[1]
        parameter_dict = readYAML(parameterFile)
        validate_input_yaml(parameter_dict)
        submit_job(parameter_dict)
    except IndexError:
        for runtype in ["bsp", "filldistance", "R"]:
            for setname in ["sbnight", "sbday", "salsanight", "salsaday"]:
                for measure in ["maximin", "maxpro"]:

                    parameter_dict = {"runtype": runtype,
                                      "setname": setname,
                                      "measure": measure,
                                      "account": "project_2000360",
                                      "email": "jjahol@utu.fi"}
                    print(parameter_dict)
                    validate_input_yaml(parameter_dict)
                    submit_job(parameter_dict)


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {(end - start):.2f} seconds.")

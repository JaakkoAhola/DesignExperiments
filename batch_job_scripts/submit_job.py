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
import itertools


def readYAML(path):
    with open(path, "r") as stream:
        try:
            output = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return output


def validate_input_yaml(submit_dict):
    assert submit_dict["runtype"] in ["bsp", "filldistance", "R"]
    assert submit_dict["setname"] in ["sbnight", "sbday", "salsanight", "salsaday"]
    assert submit_dict["measure"] in ["maximin", "maxpro"]

    if submit_dict["runtype"] in ["bsp", "R"]:
        assert isinstance(submit_dict["reps"], int)
        assert isinstance(submit_dict["designpoints"], int)


def get_runtypecode(runtype):

    runtypecode_dict = {"R": "R",
                        "filldistance": "F",
                        "bsp": "B"}

    return runtypecode_dict[runtype]


def get_setnamecode(setname):

    setnamecode_dict = {"sbnight": "bn",
                        "sbday": "bd",
                        "salsanight": "an",
                        "salsaday": "ad"
                        }

    return setnamecode_dict[setname]


def get_measurecode(measure):

    measurecode_dict = {"maximin": "M",
                        "maxpro": "P"}

    return measurecode_dict[measure]


def get_jobname(submit_dict):
    runtypecode = get_runtypecode(submit_dict["runtype"])

    setnamecode = get_setnamecode(submit_dict["setname"])

    measurecode = get_measurecode(submit_dict["measure"])

    if "designpoints" in submit_dict:
        designpoints = submit_dict["designpoints"]
    else:
        designpoints = ""

    jobname = f"{runtypecode}{setnamecode}{measurecode}{designpoints}"

    return jobname


def get_walltime(runtype):

    walltime_dict = {"bsp": "00:20:00",
                     "filldistance": "01:30:00",
                     "R": "12:00:00"}

    return walltime_dict[runtype]


def get_memory(runtype):

    memory_dict = {"bsp": "3250M",
                   "filldistance": "850M",
                   "R": "10G"}
    return memory_dict[runtype]


def get_logfile(submit_dict):

    runtype = submit_dict["runtype"]
    setname = submit_dict["setname"]
    measure = submit_dict["measure"]

    if "designpoints" in submit_dict:
        designpoints = submit_dict["designpoints"]
        designpoints = f"_{designpoints}"
    else:
        designpoints = ""

    if "reps" in submit_dict:
        reps = submit_dict["reps"]
        reps = f"_reps{reps}"
    else:
        reps = ""

    return f"logs/{runtype}/{runtype}_{setname}_{measure}{designpoints}{reps}_%j.log"


def get_command(runtype):

    command_dict = {"R": "srun apptainer_wrapper exec Rscript --no-save run_comined_eclair.R",
                    "filldistance": "srun python run_fill_distance.py",
                    "bsp": "srun python run_bsp.py"}

    return command_dict[runtype]


def get_argument(submit_dict):

    runtype = submit_dict["runtype"]
    setname = submit_dict["setname"]
    measure = submit_dict["measure"]

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
        designpoints = submit_dict["designpoints"]
        reps = submit_dict["reps"]
        argument = f"{setint} {measureint} {designpoints} {reps}"

    return argument


def get_module_and_setup(submit_dict):

    runtype = submit_dict["runtype"]
    account = submit_dict["account"]

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


def get_batch_job_script(submit_dict):

    jobname = get_jobname(submit_dict)

    email = submit_dict["email"]

    account = submit_dict["account"]

    walltime = get_walltime(submit_dict["runtype"])

    memory = get_memory(submit_dict["runtype"])

    logfile = get_logfile(submit_dict)

    module_and_setup = get_module_and_setup(submit_dict)

    command = get_command(submit_dict["runtype"])

    argument = get_argument(submit_dict)

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


def submit_job(submit_dict):
    batch_job_script = get_batch_job_script(submit_dict)

    print(batch_job_script)

    runtype = submit_dict["runtype"]
    setname = submit_dict["setname"]
    measure = submit_dict["measure"]

    if "designpoints" in submit_dict:
        designpoints = submit_dict["designpoints"]
        designpoints = f"_{designpoints}"
    else:
        designpoints = ""

    if "reps" in submit_dict:
        reps = submit_dict["reps"]
        reps = f"_{reps}"
    else:
        reps = ""

    filename = f"temp_submit_{runtype}_{setname}_{measure}{designpoints}{reps}.bash"
    with open(filename, "w") as file:
        file.write(batch_job_script)


def loop_input(parameterFile):
    parameter_dict = readYAML(parameterFile)
    print(parameter_dict)

    loop = [parameter_dict["runtype"],
            parameter_dict["setname"],
            parameter_dict["measure"]]

    if "designpoints" in parameter_dict:
        loop.append(parameter_dict["designpoints"])

    for item in itertools.product(*loop):

        if len(item) == 3:
            runtype, setname, measure = item
        elif len(item) == 4:
            runtype, setname, measure, designpoints = item

        print("prodotto", runtype, setname, measure)
        submit_dict = {"runtype": runtype,
                       "setname": setname,
                       "measure": measure,
                       "account": parameter_dict["account"],
                       "email": parameter_dict["email"]}

        if "designpoints" in parameter_dict:
            submit_dict["designpoints"] = designpoints

        if "reps" in parameter_dict:
            submit_dict["reps"] = parameter_dict["reps"]

        print(submit_dict)
        validate_input_yaml(submit_dict)
        submit_job(submit_dict)


def main():
    load_dotenv()
    try:
        parameterFile = sys.argv[1]
    except IndexError:
        print("An input yaml should be given.")

    loop_input(parameterFile)


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {(end - start):.2f} seconds.")

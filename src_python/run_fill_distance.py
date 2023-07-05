#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 4.7.2023
@licence: MIT licence Copyright
"""

import os
import pathlib
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
# package imports
from library import Data
from library import FileSystem

from algorithms import FillDistance


def main():
    load_dotenv()
    try:
        parameterFile = sys.argv[1]
        parameterDict = FileSystem.readYAML(parameterFile)
    except KeyError:
        parameterDict = {"folder": pathlib.Path(os.environ["REPO"]) /
                         "data/02_raw_output/design_stats_maximin",
                         "sobol_points_exponent_of_two": 3,
                         "design_methods_to_be_executed": ["scmc",
                                                           "comined",
                                                           "bsp",
                                                           "manuscript"],
                         "simulation_sets_to_be_executed": ['SBnight',
                                                            'SBday',
                                                            'SALSAnight',
                                                            'SALSAday'],
                         "fill_distance_filename": "filldistance_stats.csv",
                         "feasibility_ratio_filename": "feasibility_ratios.csv",
                         }

    fd = FillDistance.FillDistance(folder=eval(parameterDict["folder"]),
                                   sobol_points_exponent_of_two=parameterDict["sobol_points_exponent_of_two"],
                                   design_methods_to_be_executed=parameterDict["design_methods_to_be_executed"],
                                   simulation_sets_to_be_executed=parameterDict["simulation_sets_to_be_executed"],
                                   fill_distance_filename=parameterDict["fill_distance_filename"],
                                   feasibility_ratio_filename=parameterDict["feasibility_ratio_filename"])

    fd.get_all_sobol_hypercubes()
    fd.get_fill_distance_for_all()
    fd.join_fill_distance_stats()
    fd.save_fill_distance_csv()
    fd.get_feasibility_ratio_as_dataframe()
    fd.save_feasibility_ratio_as_dataframe()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

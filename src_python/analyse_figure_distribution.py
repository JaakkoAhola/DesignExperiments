#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 4.7.2023
@licence: MIT licence Copyright
"""

# standard imports
import os
import pathlib
import time
from datetime import datetime
from dotenv import load_dotenv

# package imports
from library import Data
from figure_analysis import DistributionAnalysis


def main():
    load_dotenv()
    optim_methods = {"maximin": pathlib.Path(os.environ["REPO"]) /
                     "data/02_raw_output/design_stats_maximin",
                     "maxpro": pathlib.Path(os.environ["REPO"]) /
                     "data/02_raw_output/design_stats_maxpro"}

    for key in optim_methods:
        dist = DistributionAnalysis.DistributionAnalysis(optim_methods[key],
                                                         key,
                                                         debug=False)
        dist.read_all_designs()
        dist.initReadFilteredSourceData()
        dist.figure_design_variable_distribution()
        dist.save_figures()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

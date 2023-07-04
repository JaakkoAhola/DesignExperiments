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
import time
from datetime import datetime

# package imports
from library import Data
from figure_analysis import FillDistanceAnalysis


def main():
    optim_methods = {"maximin": os.environ["DESIGNRESULTSMAXIMIN"],
                     "maxpro": os.environ["DESIGNRESULTSMAXPRO"]}
    for key in optim_methods:
        fill = FillDistanceAnalysis.FillDistanceAnalysis(optim_methods[key],
                                                         key)
        fill.read_all_results()
        fill.get_maximin_column_names()
        fill.reset_index()
        fill.plot_results()
        fill.save_figures()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

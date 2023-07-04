#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 4.7.2023
@licence: MIT licence Copyright
"""

import os
import sys
import time
from datetime import datetime

sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data
from figure_analysis import MaximinAnalysis


def main():
    dd = MaximinAnalysis.MaximinAnalysis()

    update_results = False

    if update_results:
        dd.get_manuscript_results()
        dd.get_maximin_results_with_R()
        dd.save_results_with_R()

    dd.read_all_results()
    dd.get_maximin_column_names()
    dd.reset_index()
    dd.sort_by_design_points()
    dd.get_maximum_values_of_maximins()
    dd.normalise_maximin_results_based_on_maximum()
    dd.plot_results()
    dd.save_figures()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

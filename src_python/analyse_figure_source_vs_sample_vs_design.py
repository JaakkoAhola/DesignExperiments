#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 4.7.2023
@licence: MIT licence Copyright
"""

import time
from datetime import datetime
from dotenv import load_dotenv
# package imports
from library import Data
from figure_analysis import SourceVsSampleVsDesignAnalysis


def main():
    load_dotenv()
    comp = SourceVsSampleVsDesignAnalysis.SourceVsSampleVsDesignAnalysis()

    if False:
        comp.figure_source_vs_sample_vs_designs_bar_plot()
    if True:
        comp.figure_scatter_plot_projections()

    comp.finalise_figures()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")

    main()

    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

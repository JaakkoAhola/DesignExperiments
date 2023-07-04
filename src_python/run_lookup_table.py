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
import numpy
import pandas
# package imports
from library import Data
from algorithms import LookUpTable


def main():
    look = LookUpTable.LookUpTable(True)
    print(look.function_look_up_table("q_inv", 1))
    hypercube = pandas.DataFrame(data=numpy.random.rand(100, 6),
                                 columns=['q_inv', 'tpot_inv', 'lwp', 'tpot_pbl', 'pbl', 'cdnc'])

    up = look.upscale_dataframe(hypercube)
    print(up)
    look.load_collection()
    for key in up.columns:
        print(f"{key} {up[key].min():.2f} {up[key].max():.2f} collection {look.get_collection_dataframe()[key].min():.2f} {look.get_collection_dataframe()[key].max():.2f}")

    print()
    print(look.function_downscale_value("q_inv", -1, estimate_function=look.down_scale_mean))

    print()
    start = time.time()
    print(look.downscale_dataframe(look.get_collection_dataframe(), estimate_function=look.down_scale_mean))
    end = time.time()
    print(f"Downscaling log search,  mean {end-start} seconds")

    print()
    start = time.time()
    print(look.downscale_dataframe(look.get_collection_dataframe(),
          estimate_function=look.down_scale_linearfit))
    end = time.time()
    print(f"Downscaling log search, linfit {end-start} seconds")


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

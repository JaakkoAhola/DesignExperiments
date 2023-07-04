#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 4.7.2023
@licence: MIT licence Copyright
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
# package imports
from library import Data
from algorithms import BinarySpacePartition


def main():
    load_dotenv()
    bsp = BinarySpacePartition.BinarySpacePartition(design_points=10,
                                                    outputfile=os.environ["DESIGNRESULTS"] + "/design_stats/test/bsp_test.csv")

    bsp.create_bs_partitions()

    bsp.sample_partitions_to_design()

    bsp.write_design()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

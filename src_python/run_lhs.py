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
from algorithms import LatinHyperCubeSampleDesign


def main():
    load_dotenv()
    lhs_design = LatinHyperCubeSampleDesign.LatinHyperCubeSampleDesign()
    lhs_design.get_full_design_lhs()

    # constraints
    lhs_design.get_humidity_jump()
    lhs_design.get_pblh_in_meters()
    lhs_design.get_humidity_jump_in_grams()
    lhs_design.check_humidity_constraint()

    lhs_design.write_design_latin()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

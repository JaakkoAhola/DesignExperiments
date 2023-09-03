#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 28.7.2023
@licence: MIT licence Copyright
"""

import time
from datetime import datetime
from dotenv import load_dotenv
import sys

# package imports
from library import Data
from algorithms import LookUpTable


def main(variable):
    load_dotenv()
    look = LookUpTable.LookUpTable(variable=variable, debug=False)
    look.create_look_up_tables()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    try:
        variable = sys.argv[1:]
        assert isinstance(variable, list)
    except KeyError:
        variable = None
    if len(variable) == 0:
        variable = None

    main(variable)
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 5.7.2023
@licence: MIT licence Copyright
"""

import time
from datetime import datetime
import pandas


def main():
    number_of_samples = 20000
    df = pandas.read_csv("data/01_source/eclair_dataset_2001_designvariables.csv",
                         index_col=0)

    sample = df.sample(number_of_samples,
                       random_state=321)

    sample.to_csv(f"data/01_source/sample{number_of_samples}.csv")


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {(end - start):.2f} seconds.")

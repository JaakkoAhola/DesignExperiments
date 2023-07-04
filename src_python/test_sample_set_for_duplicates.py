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
import pandas


def main():
    load_dotenv()
    root_file = os.getenv("DESIGNRESULTS") + "eclair_dataset_2001_designvariables.csv"
    columns = ['q_inv', 'tpot_inv', 'lwp', 'tpot_pbl', 'pbl', 'cdnc', 'ks', 'as', 'cs',
               'rdry_AS_eff', 'cos_mu']
    for col in columns:

        base = f'{os.getenv("DESIGNRESULTS")}/eclair_dataset_2001_designvariables_look_up_table_{col}.csv'
        df = pandas.read_csv(base)
        tot = len(df)
        for ind in range(1, tot):
            back = df.iloc[ind - 1][col]
            forth = df.iloc[ind][col]
            k = 0
            if back >= forth:
                k += 1
        print(col, k)

        dup = len(df[col][df[col].duplicated()])

        print(f"{col} {dup} {dup/tot*100:.2f}")


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {(end - start)}")

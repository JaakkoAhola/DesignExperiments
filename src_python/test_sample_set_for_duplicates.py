#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 4.7.2023
@licence: MIT licence Copyright
"""

import os
import pathlib
import time
from datetime import datetime
from dotenv import load_dotenv
import pandas


def main():
    load_dotenv()
    columns = ['q_inv', 'tpot_inv', 'lwp', 'tpot_pbl', 'pbl', 'cdnc', 'ks', 'as', 'cs',
               'rdry_AS_eff', 'cos_mu']
    use_sample_set = False
    check_original_look_up_tables = False

    if use_sample_set:
        prefix = "sample20000"
    else:
        prefix = "eclair_dataset_2001_designvariables"

    if check_original_look_up_tables:
        suffix = "_look_up_table_"
    else:
        suffix = "_look_up_table_non_duplicate_"

    for col in columns:

        base = pathlib.Path(os.environ["REPO"]) / \
            f"data/01_source/{prefix}{suffix}{col}.csv"
        df = pandas.read_csv(base)
        tot = len(df)
        # for ind in range(1, tot):
        #     back = df.iloc[ind - 1][col]
        #     forth = df.iloc[ind][col]
        #     k = 0
        #     if back >= forth:
        #         k += 1
        # # print(col, k)

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

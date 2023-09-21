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
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import pandas
import numpy
from library import Data


def reshape_list(arr):
    if isinstance(arr, pandas.core.frame.DataFrame):
        arr = arr.values.reshape(1, -1)
    elif isinstance(arr, pandas.core.series.Series):
        arr = arr.values
    else:
        pass

    arr = arr.ravel()

    return arr


def is_array_unique_show_duplicates(arr, epsilon=Data.getEpsilon()):
    arr = reshape_list(arr)

    # Calculate the absolute differences between all pairs of elements
    differences = numpy.abs(numpy.subtract.outer(arr, arr))

    # Set the diagonal elements to infinity to avoid comparing elements to themselves
    differences[numpy.triu_indices(len(arr), 0)] = numpy.inf
    smaller_than_epsilon = differences < epsilon
    indices = numpy.argwhere(smaller_than_epsilon)
    duplicate_indices = numpy.unique(indices.flatten())

    # Check if all differences are less than epsilon
    return numpy.all(smaller_than_epsilon), duplicate_indices


def simple_diff(arr, epsilon=Data.getEpsilon()):
    arr = reshape_list(arr)
    forward_values = arr[1:]
    backward_values = arr[:-1]
    differences = numpy.abs(forward_values - backward_values)
    smaller_than_epsilon = differences < epsilon
    indices = numpy.argwhere(smaller_than_epsilon)
    duplicate_indices = numpy.unique(numpy.concatenate((indices, indices + 1)))

    return numpy.all(smaller_than_epsilon), duplicate_indices


def main():
    load_dotenv()
    columns = ['q_inv', 'tpot_inv', 'lwp', 'tpot_pbl', 'pbl', 'cdnc', 'ks', 'as', 'cs',
               'rdry_AS_eff', 'cos_mu']

    mountfolder = pathlib.Path(
        "/home/jamesaloha/mounttauskansiot/puhtiwork/optimal_design/DesignExperiments")
    mounted = (mountfolder / ".env").is_file()

    if mounted:
        rootfolder = "/home/jamesaloha/mounttauskansiot/puhtiwork/optimal_design/DesignExperiments"
    else:
        rootfolder = os.environ["REPO"]

    if len(sys.argv) >= 3:
        use_sample_set = sys.argv[1].lower() == "true"
        check_original_look_up_tables = sys.argv[2].lower() == "true"
    else:
        use_sample_set = True
        check_original_look_up_tables = False

    if use_sample_set:
        setname = "sample20000"
    else:
        setname = "eclair_dataset_2001_designvariables"

    if check_original_look_up_tables:
        subdir = "archive_lookuptable/"
    else:
        subdir = ""

    # data_type = "float64"
    pref = "_look_up_table_"
    print()
    for epsilon in [1e-3, 1e-6, 1e-8, 1e-12, Data.getEpsilon()]:
        print()
        print()
        print(epsilon)
        for col in columns:

            base = pathlib.Path(rootfolder) / \
                f"data/01_source/{subdir}{setname}{pref}{col}.csv"

            assert base.is_file(), f"File {base} missing, check your folders"

            print("file", base)
            df = pandas.read_csv(base)
            total_number_of_samples = len(df)

            is_unique, duplicate_indices = simple_diff(df, epsilon)

            if (not use_sample_set) and (not check_original_look_up_tables) and (not mounted):
                df.iloc[duplicate_indices].to_csv(pathlib.Path(os.environ["REPO"]) /
                                                  f"data/01_source/duplicates/{setname}{col}_duplicates.csv")
            # print(col, k)
            # df[col][df[col].duplicated()].to_csv(pathlib.Path(os.environ["REPO"]) /
            #                                      f"data/{data_type}_{col}_dup.csv", index_col=False)
            # dup = len(df[col][df[col].duplicated()])
            number_of_duplicates = len(duplicate_indices)

            print(f"{col}: {epsilon:e} Unique {is_unique}. \
Number of duplicates {number_of_duplicates}. \
Percentage of duplicates {number_of_duplicates/total_number_of_samples*100:.2f}")
            print()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {(end - start)}")

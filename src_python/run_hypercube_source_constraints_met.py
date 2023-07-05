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
import pathlib
from datetime import datetime
from dotenv import load_dotenv
# 3rd party imports
import pandas
# package imports
from library import Data
from library import Meteo
from algorithms import LookUpTable


def main():
    load_dotenv()
    look = LookUpTable.LookUpTable()

    collection_filename = pathlib.Path(os.environ["REPO"]) / \
        "data/01_source/eclair_dataset_2001_designvariables.csv"

    pure_hypercube_collection_filename = pathlib.Path(os.environ["REPO"]) / \
        "data/02_raw_output/hypercube_eclair_dataset_2001_designvariables_constraints_met.csv"

    start = time.time()
    dataframe = pandas.read_csv(collection_filename, index_col=0)
    print(f"datafile read in {time.time()-start} seconds")
    start = time.time()
    print("solving rw")
    dataframe["aux_q_pbl_kg_kg"] = dataframe.apply(lambda row:
                                                   Meteo.solve_rw_lwp(101780,
                                                                      row["tpot_pbl"],
                                                                      row["lwp"] *
                                                                      1e-3,
                                                                      row["pbl"] * 100.),
                                                   axis=1)
    print(f"rw solved in {time.time()-start} seconds")

    dataframe["aux_q_pbl_g_kg"] = dataframe["aux_q_pbl_kg_kg"] * 1e3
    print("solving q constraint")
    start = time.time()
    dataframe["q_constraint"] = dataframe.apply(lambda row:
                                                row["aux_q_pbl_g_kg"] -
                                                row["q_inv"] > 1,
                                                axis=1)
    print(f"solved q constraint in {time.time()-start} seconds")
    print("checking number of violations")
    violations = dataframe.loc[lambda df: df["q_constraint"] is False].shape[0]
    pure = dataframe.loc[lambda df: df["q_constraint"] is True]
    print("making the hypercube")
    start = time.time()
    pure_hypercube = look.downscale_dataframe(pure)
    print(f"hypercube made in {time.time()-start} seconds")
    total = dataframe.shape[0]
    print(f"constraint violations {violations}, fraction {violations/total}")
    print("saving pure collection")
    pure_hypercube.csv(pure_hypercube_collection_filename)


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

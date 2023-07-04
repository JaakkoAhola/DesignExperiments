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
import pathlib
import pandas
from dotenv import load_dotenv
# package imports
from library import Data
from library import Meteo


def main():
    load_dotenv()
    datarootfolder = pathlib.Path(os.environ["DATAT"])
    mainfolder = datarootfolder / "ECLAIR"

    collection_filename = mainfolder / "eclair_dataset_2001_designvariables.csv"

    pure_collection_filename = mainfolder / "eclair_dataset_2001_designvariables_constraints_met.csv"

    dataframe = pandas.read_csv(collection_filename, index_col=0)
    print("solving rw")
    dataframe["aux_q_pbl_kg_kg"] = dataframe.apply(lambda row:
                                                   Meteo.solve_rw_lwp(101780,
                                                                      row["tpot_pbl"],
                                                                      row["lwp"] * 1e-3,
                                                                      row["pbl"] * 100.),
                                                   axis=1)
    dataframe["aux_q_pbl_g_kg"] = dataframe["aux_q_pbl_kg_kg"] * 1e3
    print("solving q constraint")
    dataframe["q_constraint"] = dataframe.apply(lambda row:
                                                row["aux_q_pbl_g_kg"] - row["q_inv"] > 1,
                                                axis=1)
    print("checking number of violations")
    violations = dataframe.loc[lambda df: df["q_constraint"] == False].shape[0]
    pure = dataframe.loc[lambda df: df["q_constraint"] == True]
    total = dataframe.shape[0]
    print(f"constraint violations {violations}, fraction {violations/total}")
    print("saving pure collection")
    pure.csv(pure_collection_filename)


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

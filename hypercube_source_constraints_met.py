#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
import os
import sys
import time
from datetime import datetime
import pandas
sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data
sys.path.append(os.environ["CODEX"] + "/LES-superfolder/LES-emulator-02postpros")
import LES2emu
import pathlib
from LookUpTable import LookUpTable

def main():
    look = LookUpTable()
    datarootfolder = pathlib.Path(os.environ["DATAT"])
    mainfolder = datarootfolder / "ECLAIR"

    collection_filename = mainfolder / "eclair_dataset_2001_designvariables.csv"

    pure_hypercube_collection_filename = mainfolder / "hypercube_eclair_dataset_2001_designvariables_constraints_met.csv"
    start = time.time()
    dataframe =  pandas.read_csv(collection_filename, index_col=0)
    print(f"datafile read in {time.time()-start} seconds")
    start = time.time()
    print("solving rw")
    dataframe["aux_q_pbl_kg_kg"] = dataframe.apply(lambda row:
                                                    LES2emu.solve_rw_lwp( 101780,
                                                                         row["tpot_pbl"],
                                                                         row["lwp"]*1e-3,
                                                                         row["pbl"]*100.),
                                                                         axis = 1)
    print(f"rw solved in {time.time()-start} seconds")

    dataframe["aux_q_pbl_g_kg"] = dataframe["aux_q_pbl_kg_kg"]*1e3
    print("solving q constraint")
    start = time.time()
    dataframe["q_constraint"] = dataframe.apply(lambda row:
                                                        row["aux_q_pbl_g_kg"] - row["q_inv"] > 1 ,
                                                        axis = 1)
    print(f"solved q constraint in {time.time()-start} seconds")
    print("checking number of violations")
    violations = dataframe.loc[lambda df: df["q_constraint"] == False].shape[0]
    pure = dataframe.loc[lambda df: df["q_constraint"] == True]
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

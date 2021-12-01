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

sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data
sys.path.append(os.environ["CODEX"] + "/LES-superfolder/LES-emulator-02postpros")
import LES2emu
import pathlib

def main():
    datarootfolder = pathlib.Path(os.environ["DATAT"])
    mainfolder = datarootfolder / "ECLAIR"

    collection_filename = mainfolder / "eclair_dataset_2001_designvariables.csv"

    dataframe =  pandas.read_csv(collection_filename, index_col=0)

    dataframe["aux_q_pbl_kg_kg"] = dataframe.apply(lambda row:
                                                    LES2emu.solve_rw_lwp( 101780,
                                                                         row["tpot_pbl"],
                                                                         row["lwp"]*1e-3,
                                                                         row["pbl"]*100.),
                                                                         axis = 1)
    dataframe["aux_q_pbl_g_kg"] = dataframe["aux_q_pbl_kg_kg"]*1e3

    dataframe["q_constraint"] = dataframe.apply(lambda row:
                                                        row["aux_q_pbl_g_kg"] - row["q_inv"] > 1 ,
                                                        axis = 1)

    violations = dataframe[dataframe["q_constraint"]].shape[0]
    total = dataframe.shape[0]
    print(f"constraint violations {violations}, fraction {violations/total}")



if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")
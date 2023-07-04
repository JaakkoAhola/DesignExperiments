#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 4.7.2023
@licence: MIT licence Copyright
"""

import os
import sys
import time
from datetime import datetime
import numpy
import pandas

# package imports
from library import Data
from algorithms import MaximinDesignWithGeneticAlgorithm


def main():
    """  sys.argv[1] index of design 0: SBnight
                                     1: SBday
                                     2: SALSAnight
                                     3: SALSAday
                                if non-existent, run in debug mode

"""
    debug = False

    try:
        indeksi = int(sys.argv[1])
    except IndexError:
        print("Not getting a cmd-line argument, switching to debug mode")
        debug = True

    design_variables = {"SBnight": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc"],
                        "SBday": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc", "cos_mu"],
                        "SALSAnight": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff"],
                        "SALSAday": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff", "cos_mu"]}

    if debug:
        file = os.environ["DATAT"] + "/ECLAIR/sample20000.csv"
        keys_list = list(design_variables)[:1]
        design_points_vector = numpy.array([5])
    else:
        file = os.environ["DATAT"] + "/ECLAIR/eclair_dataset_2001_designvariables.csv"
        keys_list = [list(design_variables)[indeksi]]
        design_points_vector = numpy.array([53, 101, 199, 307, 401, 499])

    for key in keys_list:
        solutions_ga = numpy.zeros(numpy.shape(design_points_vector))
        timing_vector_ga = numpy.zeros(numpy.shape(design_points_vector))

        if debug:
            subfolder = "test"
        else:
            subfolder = key

        for ind, design_points in enumerate(design_points_vector):
            ga_design = MaximinDesignWithGeneticAlgorithm.MaximinDesignWithGeneticAlgorithm(design_variables=design_variables[key],
                                                                                            design_points=design_points,
                                                                                            sourcefile=file,
                                                                                            outputfile=os.environ["DATAT"] + "/ECLAIR/design_stats/" + subfolder + "/ga/ga_" + str(design_points) + ".csv")

            if debug:
                df = ga_design.get_dataframe()
                subsample = df.sample(10, random_state=0)
                ga_design.set_dataframe(subsample)

            start = time.time()
            ga_design.optimise()
            duration_ga = time.time() - start
            timing_vector_ga[ind] = duration_ga
            solutions_ga[ind] = -ga_design.get_objective_value()

            ga_design.get_design()
            if ga_design.get_design().shape[0] != design_points:
                print("ValueError not the desired amount of design_points")
                continue
            ga_design.write_design()

        solutions_df = pandas.DataFrame(data={
            "maximin_ga": solutions_ga,
            "duration_ga": timing_vector_ga,
        },
            index=design_points_vector)
        solutions_df.index.name = "design_points"
        solutions_df.to_csv(os.environ["DATAT"] +
                            "/ECLAIR/design_stats/" + subfolder + "/ga_stats.csv")


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

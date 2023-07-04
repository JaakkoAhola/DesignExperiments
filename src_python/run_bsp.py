#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 3.7.2023
@licence: MIT licence Copyright
"""

import os
import sys
import time
import numpy
import pandas
from datetime import datetime

sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data

from algorithms import BinarySpacePartition
from algorithms import LookUpTable
from library import Metrics


def main():
    """  sys.argv[1] index of design 0: SBnight
                                     1: SBday
                                     2: SALSAnight
                                     3: SALSAday
        sys.argv[2] use_max_pro integer 0: use maximin measure
                                        1: use MaxPro measure

"""

    debug = False

    try:
        indeksi = int(sys.argv[1])
    except IndexError:
        print("Not getting a cmd-line argument, switching to debug mode")
        debug = True

    meteorological_variables = ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl"]
    sb_variables = ["cdnc"]
    salsa_variables = ["ks", "as", "cs", "rdry_AS_eff"]
    daytime_variables = ["cos_mu"]

    design_variables = {"SBnight": meteorological_variables + sb_variables,
                        "SBday": meteorological_variables + sb_variables + daytime_variables,
                        "SALSAnight": meteorological_variables + salsa_variables,
                        "SALSAday": meteorological_variables + salsa_variables + daytime_variables}

    if debug:
        file = os.environ["DATAT"] + "/ECLAIR/sample20000.csv"
        keys_list = list(design_variables)[:1]
        design_points_vector = numpy.array([5])
    else:
        file = os.environ["DATAT"] + "/ECLAIR/eclair_dataset_2001_designvariables.csv"
        keys_list = [list(design_variables)[indeksi]]
        design_points_vector = numpy.array([53, 101, 199, 307, 401, 499])

    look = LookUpTable.LookUpTable()
    if not debug:
        try:
            use_max_pro = bool(int(sys.argv[2]))
        except IndexError:
            sys.exit("Did not get a integer-boolean cmd-line argument for use_max_pro")
    else:
        use_max_pro = False

    if use_max_pro:
        upfolder = "maxpro"
    else:
        upfolder = "maximin"

    for key in keys_list:
        solutions_bsp = numpy.zeros(numpy.shape(design_points_vector))
        timing_vector_bsp = numpy.zeros(numpy.shape(design_points_vector))

        if debug:
            subfolder = "test"
        else:
            subfolder = key

        for ind, design_points in enumerate(design_points_vector):
            if not use_max_pro:
                best = -numpy.inf
            else:
                best = numpy.inf

            start = time.time()
            print(" ")
            print(" ")
            print("design_points", design_points)
            for k in range(1):
                print("iteration:", k)
                bsp = BinarySpacePartition(design_variables=design_variables[key],
                                           design_points=design_points,
                                           sourcefile=file,
                                           outputfile=os.environ["DATAT"] + "/ECLAIR/design_stats_" + upfolder + "/" + subfolder + "/bsp/bsp_" + str(design_points) + ".csv")

                bsp.create_bs_partitions()
                bsp.sample_partitions_to_design()
                upscaled_design = bsp.get_design()
                hypercube_design = look.downscale_dataframe(upscaled_design)
                bsp_matrix = numpy.asarray(hypercube_design)

                if not use_max_pro:
                    solution = Metrics.matrix_minimum_distance(bsp_matrix)

                    if solution > best:
                        best = solution
                        bsp.write_design()

                else:
                    solution = Metrics.max_pro_measure(bsp_matrix)

                    if solution < best:
                        best = solution
                        bsp.write_design()

            duration_bsp = time.time() - start

            solutions_bsp[ind] = best
            timing_vector_bsp[ind] = duration_bsp

        df_key = upfolder + "_bsp"
        solutions_df = pandas.DataFrame(data={
            df_key: solutions_bsp,
            "duration_bsp": timing_vector_bsp,
        },
            index=design_points_vector)
        solutions_df.index.name = "design_points"

        solutions_df.to_csv(os.environ["DATAT"] + "/ECLAIR/design_stats_" +
                            upfolder + "/" + subfolder + "/bsp_stats.csv")


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")
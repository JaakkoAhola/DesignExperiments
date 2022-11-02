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
import random
from copy import deepcopy
from datetime import datetime
import numpy
import pandas

sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data
import MaximinDesign
from LookUpTable import LookUpTable
sys.path.append(os.environ["CODEX"] + "/LES-superfolder/LES-emulator-02postpros")
import LES2emu


class BinarySpacePartition:

    def __init__(self,
                 design_variables=['q_inv', 'tpot_inv', 'lwp', 'tpot_pbl', 'pbl', 'cdnc'],
                 design_points=500,
                 sourcefile=os.environ["DESIGNRESULTS"] + "/sample20000.csv",
                 outputfile=os.environ["DESIGNRESULTS"] + "/bsp_test_sb_night_500.csv"
                 ):

        self.design_variables = design_variables

        self.collection = None

        self.collection = pandas.read_csv(sourcefile, index_col=0)[self.design_variables]

        if ("cos_mu" in self.design_variables):
            self.collection = self.collection[self.collection["cos_mu"] > Data.getEpsilon()]

        self.design_points = design_points

        self.partitions = []

        self.design = None

        self.outputfile = outputfile
        self.outputfolder = os.path.dirname(self.outputfile)
        os.makedirs(self.outputfolder, exist_ok=True)

    def set_collection(self, dataframe):
        self.collection = dataframe

    def set_design_points(self, design_points):
        self.design_points = design_points

    def set_design_variables(self, design_variables):
        self.design_variables = design_variables

    def shuffleList(self, array):
        shuffledArray = deepcopy(array)

        random.shuffle(shuffledArray)

        return shuffledArray

    def create_bs_partitions(self):
        self.partitions = [self.collection]

        make_partition = True
        print("Creating partitions")
        print("\t", end="")
        while make_partition:
            shuffled_dimensions = self.shuffleList(self.design_variables)
            for dim_ind, dimension in enumerate(shuffled_dimensions):
                part_ind = 0
                iterate_partitions = True
                while iterate_partitions:
                    print(f"{len(self.partitions)}", end=" ")
                    if len(self.partitions) < self.design_points:
                        partition = self.partitions[part_ind]

                        if len(partition) == 1:
                            part_ind += 1
                            continue

                        median = len(partition) // 2
                        bin_zero = partition.sort_values(by=dimension).iloc[:median]
                        bin_one = partition.sort_values(by=dimension).iloc[median:]

                        self.partitions[part_ind] = bin_zero
                        self.partitions.insert(part_ind + 1, bin_one)

                    else:
                        make_partition = False

                    part_ind += 2

                    iterate_partitions = (make_partition and (part_ind < len(self.partitions)))

    def sample_partitions_to_design(self):
        design_helper_list = [None] * self.design_points
        print("Sampling partitions")
        print("\t", end="")
        for part_ind, partition in enumerate(self.partitions):
            constraintPass = False
            print(f"{part_ind}", end=" ")
            while not constraintPass:
                row = partition.sample(random_state=321)
                q_pbl = LES2emu.solve_rw_lwp(101780,
                                             row.iloc[0]["tpot_pbl"],
                                             row.iloc[0]["lwp"] * 1e-3,
                                             row.iloc[0]["pbl"] * 100.) * 1e3
                constraintPass = (q_pbl - row.iloc[0]["q_inv"] > 1)

            design_helper_list[part_ind] = row

        self.design = pandas.concat(design_helper_list)
        return self.design

    def get_design(self):
        return self.design

    def write_design(self):
        self.design.to_csv(self.outputfile)


def main():
    testing = False
    if testing:
        bsp = BinarySpacePartition(design_points=10,
                                   outputfile=os.environ["DESIGNRESULTS"] + "/design_stats/test/bsp_test.csv")
        bsp.create_bs_partitions()

        bsp.sample_partitions_to_design()
        bsp.write_design()
        sys.exit()

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

    look = LookUpTable()
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
                    solution = MaximinDesign.matrix_minimum_distance(bsp_matrix)

                    if solution > best:
                        best = solution
                        bsp.write_design()

                else:
                    solution = MaximinDesign.max_pro_measure(bsp_matrix)

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

        solutions_df.to_csv(os.environ["DATAT"] + "/ECLAIR/design_stats_" + upfolder + "/" + subfolder + "/bsp_stats.csv")


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

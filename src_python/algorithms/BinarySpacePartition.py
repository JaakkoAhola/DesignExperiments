#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
import os
import random
from copy import deepcopy
import pathlib
import pandas

# package imports
from library import Data
from library import Meteo


class BinarySpacePartition:

    def __init__(self,
                 design_variables=['q_inv', 'tpot_inv', 'lwp', 'tpot_pbl', 'pbl', 'cdnc'],
                 design_points=500,
                 sourcefile=pathlib.Path(os.environ["REPO"]) / "data/01_source/sample20000.csv",
                 outputfile=pathlib.Path(os.environ["REPO"]) /
                 "data/02_raw_output/bsp_test_sb_night_500.csv"
                 ):

        self.design_variables = design_variables

        self.design_points = design_points

        self.collection = pandas.read_csv(sourcefile, index_col=0)[self.design_variables]

        if "cos_mu" in self.design_variables:
            self.collection = self.collection[self.collection["cos_mu"] > Data.getEpsilon()]

        self.outputfile = outputfile
        self.outputfolder = os.path.dirname(self.outputfile)
        os.makedirs(self.outputfolder, exist_ok=True)

        self.partitions = []

        self.design = None

        random.seed(321)

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
            for _, dimension in enumerate(shuffled_dimensions):
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
        print("")

    def sample_partitions_to_design(self):
        design_helper_list = [None] * self.design_points
        print("Sampling partitions")
        print("\t", end="")
        for part_ind, partition in enumerate(self.partitions):
            constraintPass = False
            print(f"{part_ind}", end=" ")
            random_seed_increment = 0
            print("(", end=" ")
            while not constraintPass:
                print(f"{random_seed_increment}", end=" ")
                row = partition.sample(random_state=part_ind + random_seed_increment)
                q_pbl = Meteo.solve_rw_lwp(101780,
                                           row.iloc[0]["tpot_pbl"],
                                           row.iloc[0]["lwp"] * 1e-3,
                                           row.iloc[0]["pbl"] * 100.) * 1e3
                constraintPass = (q_pbl - row.iloc[0]["q_inv"] > 1)
                random_seed_increment += 1
            print(")", end=" ")

            design_helper_list[part_ind] = row

        self.design = pandas.concat(design_helper_list)
        print(" ")
        print(" ")
        return self.design

    def get_design(self):
        return self.design

    def write_design(self):
        self.design.to_csv(self.outputfile)

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

import pandas

sys.path.append(os.environ["LESMAINSCRIPTS"])
from SourceVsSampleVsDesign import SourceVsSampleVsDesign
from Data import Data


class BinarySpacePartition:

    def __init__(self,
                 design_variables = ['q_inv', 'tpot_inv', 'lwp', 'tpot_pbl', 'pbl', 'cdnc'],
                 number_of_samples_required = 500,
                 file = "/home/aholaj/Data/ECLAIR/sb_sb_night_500.csv"
                 ):

        self.design_variables = design_variables

        self.collection = None

        self.number_of_samples_required = number_of_samples_required


        self._load_collection()

        self.partitions = []

        self.design = None

        self.file = file


    def _load_collection(self):
        latin = SourceVsSampleVsDesign()
        latin.get_sample()

        self.collection = deepcopy(latin.get_sample()[self.design_variables])

        return self.collection

    def set_collection(self, dataframe):
        self.collection = dataframe

    def set_number_of_samples_required(self, design_points):
        self.number_of_samples_required = design_points

    def set_design_variables(self, design_variables):
        self.design_variables = design_variables

    def shuffleList(self, array):
        shuffledArray = deepcopy(array)
        random.seed(787)
        random.shuffle(shuffledArray)

        return shuffledArray

    def create_bs_partitions(self):
        self.partitions = [self.collection]

        make_partition = True

        while make_partition:
            shuffled_dimensions = self.shuffleList( self.design_variables )
            for dim_ind, dimension in enumerate(shuffled_dimensions):
                part_ind = 0
                iterate_partitions = True
                while iterate_partitions:

                    if len(self.partitions) < self.number_of_samples_required:
                        partition = self.partitions[part_ind]

                        if len(partition) == 1:
                            part_ind += 1
                            continue

                        median = len(partition)//2
                        bin_zero = partition.sort_values(by=dimension).iloc[:median]
                        bin_one = partition.sort_values(by=dimension).iloc[median:]

                        self.partitions[part_ind] = bin_zero
                        self.partitions.insert(part_ind + 1, bin_one)

                    else:
                        make_partition = False

                    part_ind += 2

                    iterate_partitions = (make_partition and (part_ind < len(self.partitions)))

    def sample_partitions_to_design(self):
        design_helper_list = [None]*self.number_of_samples_required
        for part_ind, partition in enumerate(self.partitions):
            pass
            row = partition.sample()
            design_helper_list[part_ind] = row

        self.design = pandas.concat(design_helper_list)
        return self.design

    def get_design(self):
        return self.design

    def write_design(self):
        self.design.to_csv(self.file)



def main():
    bsp = BinarySpacePartition(number_of_samples_required = 500)
    bsp.create_bs_partitions()

    bsp.sample_partitions_to_design()
    bsp.write_design()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")
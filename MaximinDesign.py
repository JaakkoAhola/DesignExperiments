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
import numpy
import pandas
from datetime import datetime
from scipy.spatial import distance
sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data
from geneticalgorithm import geneticalgorithm as ga
from BinarySpacePartition import BinarySpacePartition

def logarithmic_euclidian_distance(x,y):
    x_log = numpy.log(x)
    y_log = numpy.log(y)

    return distance.euclidean(x_log, y_log)

def matrix_minimum_distance(mm, dist_func=logarithmic_euclidian_distance):
    minimum = numpy.nan

    for row in range(mm.shape[0]):
        for otherRow in range(mm.shape[0]):
            if row != otherRow:
                dd = dist_func(mm[row,], mm[otherRow])
                minimum = numpy.nanmin([dd, minimum])
    return minimum


class MaxiMinDesign:

    def __init__(self, candidate_dataframe_filename):
        self.dataframe = pandas.read_csv(candidate_dataframe_filename, index_col=0)

    def get_dataframe(self):
        return self.dataframe

    def set_dataframe(self, dataframe):
        self.dataframe = dataframe

    def set_design_points(self, design_points):
        self.design_points = design_points

    def cost(self, boolean_array):
        selection = pandas.array(boolean_array.astype("bool"))
        candidates = self.dataframe[ selection ]
        matrix = numpy.asarray(candidates)

        minimum_distance = matrix_minimum_distance(matrix)

        pen = 0.

        if numpy.sum(boolean_array) != self.design_points:
            pen = 100 + 10 * numpy.sum(boolean_array)

        return -minimum_distance + pen

    def optimise(self):

        model=ga(function=self.cost,
                 dimension=self.dataframe.shape[0],
                 variable_type='bool',
                 convergence_curve=False)

        model.run()

        self.solution = model.output_dict

        return self.solution

    def get_solution(self):
        return self.solution

    def get_objective_value(self):
        return self.solution["function"]


def main():

    ga_design = MaxiMinDesign("/home/aholaj/Data/ECLAIR/sample20000.csv")
    bsp = BinarySpacePartition()

    debug = False


    if debug:
        orig_df = pandas.read_csv("/home/aholaj/Data/ECLAIR/sample20000.csv", index_col=0)
    else:
        orig_df = pandas.read_csv("/home/aholaj/Data/ECLAIR/eclair_dataset_2001_designvariables.csv", index_col=0)


    design_variables = {"SBnight": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc"],
                        "SBday": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc", "cos_mu"],
                        "SALSAnight": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff"],
                        "SALSAday": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff", "cos_mu"]}

    for key in list(design_variables)[2:]:


        df = orig_df

        if "cos_mu" in design_variables[key]:
            df = df[df["cos_mu"] > Data.getEpsilon()]

        df_desing_variables = df[design_variables[key]]

        ga_design.set_dataframe(df_desing_variables)

        bsp.set_design_variables(design_variables[key])
        bsp.set_collection(df_desing_variables)


        if debug:

            df = ga_design.get_dataframe()
            subsample = df.sample(10, random_state=0)
            ga_design.set_dataframe(subsample)

            p_vector = numpy.array([5])

        else:
            p_vector = numpy.arange(10,500,10)

        solutions_ga = numpy.zeros(numpy.shape(p_vector))
        timing_vector_ga = numpy.zeros(numpy.shape(p_vector))

        solutions_bsp = numpy.zeros(numpy.shape(p_vector))
        timing_vector_bsp = numpy.zeros(numpy.shape(p_vector))

        for ind, p in enumerate(p_vector):
            ga_design.set_design_points(p)
            start = time.time()
            ga_design.optimise()
            duration_ga = time.time() - start
            timing_vector_ga[ind] = duration_ga
            solutions_ga[ind] = -ga_design.get_objective_value()

            bsp.set_number_of_samples_required(p)
            start = time.time()
            bsp.create_bs_partitions()
            bsp.sample_partitions_to_design()
            duration_bsp = time.time() - start
            bsp_matrix = numpy.asarray(bsp.get_design())
            solutions_bsp[ind] = matrix_minimum_distance(bsp_matrix)
            timing_vector_bsp[ind] = duration_bsp


        solutions_df = pandas.DataFrame({"design_points": p_vector,
                                         "maximin_ga": solutions_ga,
                                         "duration_ga": timing_vector_ga,
                                         "maximin_bsp": solutions_bsp,
                                         "duration_bsp": timing_vector_ga})

        solutions_df.to_csv("/home/aholaj/Data/ECLAIR/design_stats/" + key + "_design_stats.csv")



if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")
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

def generalised_distance(x_array, y_array, s=2):
    p = x_array.shape[0]

    dist = numpy.power( numpy.sum( numpy.power(numpy.abs(x_array - y_array),s) ) / p, 1/s )

    return dist


def logarithmic_euclidian_distance(x,y):
    x_log = numpy.log(x)
    y_log = numpy.log(y)

    return distance.euclidean(x_log, y_log)

def matrix_minimum_distance(mm, dist_func=generalised_distance):
    minimum = numpy.nan

    for row in range(mm.shape[0]):
        for otherRow in range(mm.shape[0]):
            if row != otherRow:
                dd = dist_func(mm[row,], mm[otherRow])
                minimum = numpy.nanmin([dd, minimum])
    return minimum


class MaxiMinDesign:

    def __init__(self,
                 design_variables=['q_inv', 'tpot_inv', 'lwp', 'tpot_pbl', 'pbl', 'cdnc'],
                 design_points=500,
                 sourcefile="/home/aholaj/Data/ECLAIR/sample20000.csv",
                 outputfile="/home/aholaj/Data/ECLAIR/bsp_test_sb_night_500.csv"
                 ):
        self.design_variables = design_variables
        self.design_points = design_points

        self.dataframe = pandas.read_csv(sourcefile, index_col=0)[self.design_variables]

        if ("cos_mu" in self.design_variables):
            self.dataframe = self.dataframe[self.dataframe["cos_mu"] > Data.getEpsilon()]

        self.outputfile = outputfile
        self.outputfolder = os.path.dirname(self.outputfile)
        os.makedirs(self.outputfolder, exist_ok=True)

        self.design = None
        self.solution = {"function":numpy.nan,
                         "variable":None}

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

        minimum_distance = 0.

        pen = 0.

        if numpy.sum(boolean_array) != self.design_points:
            pen = 500 + 10 * numpy.sum(boolean_array)
        else:
            minimum_distance = matrix_minimum_distance(matrix)

        return -minimum_distance + pen

    def optimise(self):

        model=ga(function=self.cost,
                 dimension=self.dataframe.shape[0],
                 variable_type='bool',
                 convergence_curve=False,
                 algorithm_parameters={'max_num_iteration': 10000,
                                  'population_size': 100,
                                  'mutation_probability': 0.1,
                                  'elit_ratio': 0.01,
                                  'crossover_probability': 0.5,
                                  'parents_portion': 0.3,
                                  'crossover_type': 'uniform',
                                  'max_iteration_without_improv': None})
        try:
            model.run()
            self.solution = model.output_dict
        except AssertionError:
            print("solution not found")



        return self.solution

    def get_solution(self):
        return self.solution

    def get_objective_value(self):
        return self.solution["function"]

    def get_design(self):

        if ((self.design is None) and (self.solution["variable"] is not None)):
            selection = pandas.array(self.solution["variable"].astype("bool"))

            self.design = self.dataframe[selection]

        return self.design

    def write_design(self):
        if self.design is not None:
            self.design.to_csv(self.outputfile)


def main():

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
        design_points_vector = numpy.arange(10,500,10)



    for key in keys_list:
        solutions_ga = numpy.zeros(numpy.shape(design_points_vector))
        timing_vector_ga = numpy.zeros(numpy.shape(design_points_vector))

        if debug:
            subfolder = "test"
        else:
            subfolder = key


        for ind, design_points in enumerate(design_points_vector):
            ga_design = MaxiMinDesign(design_variables=design_variables[key],
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

        solutions_df = pandas.DataFrame(data = {
                                         "maximin_ga": solutions_ga,
                                         "duration_ga": timing_vector_ga,
                                         },
                                        index=design_points_vector)
        solutions_df.index.name = "design_points"
        solutions_df.to_csv(os.environ["DATAT"] + "/ECLAIR/design_stats/" + subfolder + "/ga_stats.csv")



if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

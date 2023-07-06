#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""

# standard imports
import os
import pathlib
# 3rd party imports
import numpy
import pandas
from geneticalgorithm import geneticalgorithm as ga

# package imports
from library import Data
from library import Metrics

from dotenv import load_dotenv
load_dotenv()


class MaximinDesignWithGeneticAlgorithm:

    def __init__(self,
                 design_variables=['q_inv', 'tpot_inv',
                                   'lwp', 'tpot_pbl', 'pbl', 'cdnc'],
                 design_points=500,
                 sourcefile=pathlib.Path(os.environ["REPO"]) / "data/01_source/sample20000.csv",
                 outputfile=pathlib.Path(os.environ["REPO"]) /
                 "data/02_raw_output/bsp_test_sb_night_500.csv"
                 ):
        self.design_variables = design_variables
        self.design_points = design_points

        self.dataframe = pandas.read_csv(sourcefile, index_col=0)[
            self.design_variables]

        if ("cos_mu" in self.design_variables):
            self.dataframe = self.dataframe[self.dataframe["cos_mu"] > Data.getEpsilon(
            )]

        self.outputfile = outputfile
        self.outputfolder = os.path.dirname(self.outputfile)
        os.makedirs(self.outputfolder, exist_ok=True)

        self.design = None
        self.solution = {"function": numpy.nan,
                         "variable": None}

    def get_dataframe(self):
        return self.dataframe

    def set_dataframe(self, dataframe):
        self.dataframe = dataframe

    def set_design_points(self, design_points):
        self.design_points = design_points

    def cost(self, boolean_array):
        selection = pandas.array(boolean_array.astype("bool"))
        candidates = self.dataframe[selection]
        matrix = numpy.asarray(candidates)

        minimum_distance = 0.

        pen = 0.

        if numpy.sum(boolean_array) != self.design_points:
            pen = 500 + 10 * numpy.sum(boolean_array)
        else:
            minimum_distance = Metrics.matrix_minimum_distance(matrix)

        return -minimum_distance + pen

    def optimise(self):

        model = ga(function=self.cost,
                   dimension=self.dataframe.shape[0],
                   variable_type='bool',
                   convergence_curve=False,
                   algorithm_parameters={'max_num_iteration': 200,
                                         'population_size': 20,
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

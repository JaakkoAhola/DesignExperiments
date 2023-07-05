#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
import os
from copy import deepcopy
import pathlib
import pandas
import numpy
from scipy.stats import qmc
from scipy.spatial import distance

from algorithms import LookUpTable
from figure_analysis import MaximinAnalysis
from library import FileSystem
from library import Meteo


class FillDistance(MaximinAnalysis.MaximinAnalysis):

    def __init__(self, sobol_points_exponent_of_two=3,
                 folder=pathlib.Path(os.environ["REPO"]) /
                 "data/02_raw_output/design_stats_maximin",
                 design_methods_to_be_executed=[
                     "scmc", "comined", "bsp", "manuscript"],
                 simulation_sets_to_be_executed=[
                     'SBnight', 'SBday', 'SALSAnight', 'SALSAday'],
                 fill_distance_filename="filldistance_stats.csv",
                 feasibility_ratio_filename="feasibility_ratios.csv"):

        super().__init__(folder=folder)
        self.sobol_points_exponent_of_two = sobol_points_exponent_of_two
        self.design_methods_to_be_executed = design_methods_to_be_executed
        self.simulation_sets_to_be_executed = simulation_sets_to_be_executed
        self.fill_distance_filename = fill_distance_filename
        self.feasibility_ratio_filename = feasibility_ratio_filename

        print("")
        print("folder:", folder)
        print("sets:", simulation_sets_to_be_executed)
        print("methods:", design_methods_to_be_executed)
        print("number of sobol points:", sobol_points_exponent_of_two)
        print("")

        self.fill_distance_stats = {}
        for dd_set in self.simulation_sets_to_be_executed:
            self.fill_distance_stats[dd_set] = {}
            for method in self.design_methods_to_be_executed:
                self.fill_distance_stats[dd_set][method] = []

        self.look = LookUpTable()

        self.design_variables = {"SBnight": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc"],
                                 "SBday": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "cdnc", "cos_mu"],
                                 "SALSAnight": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff"],
                                 "SALSAday": ["q_inv", "tpot_inv", "lwp", "tpot_pbl", "pbl", "ks", "as", "cs", "rdry_AS_eff", "cos_mu"]}

        self.sobol_hypercubes_dict = {}
        for key in self.simulation_sets_to_be_executed:
            self.sobol_hypercubes_dict[key] = None

        self.feasibility_ratio = {}
        for key in self.simulation_sets_to_be_executed:
            self.feasibility_ratio[key] = None

        self.feasibility_ratio_dataframe = None

        self.joined_filldistance_stats = {}
        for key in self.simulation_sets_to_be_executed:
            self.joined_filldistance_stats[key] = None

    def get_all_sobol_hypercubes(self):

        for key in self.simulation_sets_to_be_executed:
            sobol_accepted_hypercube, feasibility_ratio = self.sobol_hypercube(
                self.design_variables[key])
            self.sobol_hypercubes_dict[key] = sobol_accepted_hypercube
            self.feasibility_ratio[key] = feasibility_ratio

    def sobol_hypercube(self, keys):
        dimensions = len(keys)
        sampler = qmc.Sobol(d=dimensions, scramble=False)
        sample = sampler.random_base2(m=self.sobol_points_exponent_of_two)

        sobol_hybercube_dataframe = pandas.DataFrame(data=sample, columns=keys)

        upscale_dataframe = self.look.upscale_dataframe(
            sobol_hybercube_dataframe)

        upscale_dataframe["constraintPass"] = upscale_dataframe.apply(lambda row: (Meteo.solve_rw_lwp(101780,
                                                                                                      row["tpot_pbl"],
                                                                                                      row["lwp"] *
                                                                                                      1e-3,
                                                                                                      row["pbl"] * 100.) * 1e3 - row["q_inv"] > 1),
                                                                      axis=1)

        sobol_hybercube_dataframe["constraintPass"] = upscale_dataframe["constraintPass"]

        sobol_accepted = deepcopy(
            sobol_hybercube_dataframe[sobol_hybercube_dataframe["constraintPass"]])
        sobol_accepted.drop(columns="constraintPass", inplace=True)

        feasibility_ratio = sobol_accepted.shape[0] / \
            upscale_dataframe.shape[0]

        return sobol_accepted, feasibility_ratio

    def get_fill_distance(self, hypercube_design_dataframe, sobol_accepted_hypercube):
        """
        the fill distance, the largest distance of any point
        in X to the closest feasible samples, is proposed as the other
        metric to assess how good the algorithm explores the feasible
        region completely.
        :return: DESCRIPTION
        :rtype: TYPE
        """
        fill_distance = -numpy.inf
        for _, sobol_row in sobol_accepted_hypercube.iterrows():
            for _, hypercube_row in hypercube_design_dataframe.iterrows():
                fill_distance = max(distance.euclidean(sobol_row.values, hypercube_row.values),
                                    fill_distance)

        return fill_distance

    def get_fill_distance_for_all(self):

        for dd_set in self.simulation_sets_to_be_executed:
            for method in self.design_methods_to_be_executed:
                subfolder = self.folder / dd_set / method
                for file_name in list(subfolder.glob("**/*.csv")):
                    design_points = int(
                        FileSystem.get_design_points_from_filename(file_name))
                    design_dataframe = pandas.read_csv(file_name, index_col=0)

                    if method in ["bsp", "manuscript"]:
                        hypercube_design_dataframe = self.look.downscale_dataframe(
                            design_dataframe)
                    else:
                        hypercube_design_dataframe = design_dataframe

                    sobol_accepted_hypercube = self.sobol_hypercubes_dict[dd_set]

                    fill_distance = self.get_fill_distance(
                        hypercube_design_dataframe, sobol_accepted_hypercube)

                    tupp = (design_points, fill_distance)
                    self.fill_distance_stats[dd_set][method].append(tupp)

        for dd_set in self.simulation_sets_to_be_executed:
            for method in self.design_methods_to_be_executed:
                list_of_tuples = self.fill_distance_stats[dd_set][method]

                self.fill_distance_stats[dd_set][method] = pandas.DataFrame.from_records(list_of_tuples,
                                                                                         columns=['design_points',
                                                                                                  'filldistance_' + method])
                self.fill_distance_stats[dd_set][method].set_index(
                    "design_points", inplace=True)

    def join_fill_distance_stats(self):
        for dd_set in self.simulation_sets_to_be_executed:
            for method in self.design_methods_to_be_executed:

                if self.joined_filldistance_stats[dd_set] is None:
                    self.joined_filldistance_stats[dd_set] = self.fill_distance_stats[dd_set][method]
                else:
                    self.joined_filldistance_stats[dd_set] = self.fill_distance_stats[dd_set][method].merge(self.joined_filldistance_stats[dd_set],
                                                                                                            how="outer",
                                                                                                            on="design_points")
            self.joined_filldistance_stats[dd_set].sort_values(
                by="design_points", inplace=True)

    def save_fill_distance_csv(self):
        for dd_set in self.simulation_sets_to_be_executed:
            self.joined_filldistance_stats[dd_set].to_csv(
                self.folder / dd_set / self.fill_distance_filename)

    def get_feasibility_ratio_as_dataframe(self):
        self.feasibility_ratio_dataframe = pandas.DataFrame.from_dict(self.feasibility_ratio,
                                                                      orient="index",
                                                                      columns=["Feasibility ratio"])

        return self.feasibility_ratio_dataframe

    def save_feasibility_ratio_as_dataframe(self):
        self.feasibility_ratio_dataframe.to_csv(
            self.folder / self.feasibility_ratio_filename)

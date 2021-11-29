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
import pathlib
import pandas
from itertools import repeat
from datetime import datetime

sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data
from Colorful import Colorful
from Figure import Figure
from PlotTweak import PlotTweak

import MaximinDesign


def get_design_points_from_filename(file_name):
    stringi = str(file_name.name)
    first = stringi.split("_")[1]

    second = first.split(".")[0]

    return second

class DesignAnalysis:

    def __init__(self,
                 folder = "/home/aholaj/mounttauskansiot/puhtiwork/ECLAIR/design_stats"):

        self.figure_folder = "/home/aholaj/Dropbox/Apps/Overleaf/väitöskirja/figures"
        self.design_sets = ["SBnight", "SBday", "SALSAnight", "SALSAday"]

        self.design_methods_with_R = ["scmc", "comined"]

        self.design_methods_python = ["bsp", "ga"]

        self.design_methods_all = self.design_methods_python + self.design_methods_with_R

        self.folder = pathlib.Path(folder)

        assert self.folder.is_dir()

        self.stats = {}
        for dd_set in self.design_sets:
            self.stats[dd_set] = {}
            for method in self.design_methods_all:
                self.stats[dd_set][method] = []

        self.joined_stats = {}
        for dd_set in self.design_sets:
            self.joined_stats[dd_set] = None

        self.figures = {}
        self.figure_width = 12/2.54

        color_list = Colorful.getDistinctColorList(["red","green","orange","blue"])

        self.method_with_color = dict(zip(self.design_methods_all, color_list))

        self.maximin_column_names = {}
        for dd_set in self.design_sets:
            self.maximin_column_names[dd_set] = []

    def get_maximin_results_with_R(self):


        for dd_set in self.stats:
            for method in self.design_methods_with_R:
                subfolder = self.folder / dd_set / method
                for file_name in list(subfolder.glob("**/*.csv")):
                    design_points = get_design_points_from_filename(file_name)
                    maximin = MaximinDesign.matrix_minimum_distance(pandas.read_csv(file_name).values)
                    tupp = (design_points, maximin)
                    self.stats[dd_set][method].append(tupp)

        for dd_set in self.design_sets:
            for method in self.design_methods_with_R:
                list_of_tuples = self.stats[dd_set][method]

                self.stats[dd_set][method] = pandas.DataFrame.from_records(list_of_tuples,
                                                                           columns =['design_points',
                                                                                     'maximin_' + method])
                self.stats[dd_set][method].set_index("design_points", inplace = True)

    def save_results_with_R(self):
        for dd_set in self.design_sets:
            for method in self.design_methods_with_R:
                stats_file = self.folder / dd_set / (method + "_stats.csv")
                self.stats[dd_set][method].to_csv(stats_file)


    def read_all_results(self):

        for dd_set in self.design_sets:
            for method in self.design_methods_all:
                stats_file = self.folder / dd_set / (method + "_stats.csv")
                assert stats_file.is_file()

                df = pandas.read_csv(stats_file, index_col = 0 )

                if self.joined_stats[dd_set] is None:
                    self.joined_stats[dd_set] = df
                else:
                    self.joined_stats[dd_set] = df.merge(self.joined_stats[dd_set], how="outer", on="design_points")


    def reset_index(self):
        for dd_set in self.design_sets:
            self.joined_stats[dd_set].reset_index(inplace=True)

    def sort_by_design_points(self):
        for dd_set in self.design_sets:
            self.joined_stats[dd_set].sort_values(by="design_points",
                                                  inplace=True)
            print(self.joined_stats[dd_set])
    def get_maximin_column_names(self):
        for dd_set in self.joined_stats:
            for column_name in self.joined_stats[dd_set].columns:
                splitted = column_name.split("_")
                if splitted[1] in  ["ga", "bsp"]:
                    continue

                if splitted[0] == "maximin":
                    self.maximin_column_names[dd_set].append(column_name)

        for dd_set in self.design_sets:
            print(dd_set)
            for method_result in self.maximin_column_names[dd_set]:
                print(f"{dd_set} {method_result} min: {numpy.log(self.joined_stats[dd_set][method_result].min()):.1f} max: {numpy.log(self.joined_stats[dd_set][method_result].max()):.1f}")




    def plot_results(self):
        self.figures["maximin"] = Figure(self.figure_folder,"maximin",
                                        figsize=[self.figure_width, 6],
                                        ncols=2,
                                        nrows=2)

        fig = self.figures["maximin"]

        for dd_ind, dd_set in enumerate(list(self.design_sets)):
            current_axis = fig.getAxes(dd_ind)

            for method_column in self.maximin_column_names[dd_set]:
                method_name = method_column.split("_")[1]
                df = self.joined_stats[dd_set]
                df.plot.line(
                            x="design_points",
                            y=method_column,
                            ax = current_axis,
                            color = self.method_with_color[method_name],
                            legend = False,
                            )



    def save_figures(self):

        for fig in self.figures.values():
            fig.save(file_extension = ".pdf")





def main():
    dd = DesignAnalysis()

    get_R_results = False

    if get_R_results:
        dd.get_maximin_results_with_R()
        dd.save_results_with_R()

    dd.read_all_results()
    dd.get_maximin_column_names()
    dd.reset_index()
    dd.sort_by_design_points()
    dd.plot_results()
    dd.save_figures()

if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")
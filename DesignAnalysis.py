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
import random
from LookUpTable import LookUpTable

def get_design_points_from_filename(file_name):
    stringi = str(file_name.name)
    first = stringi.split("_")[1]

    second = first.split(".")[0]

    return second

class DesignAnalysis:

    def __init__(self,
                 folder = os.environ["DESIGNRESULTSMAXIMIN"],
                 ):

        self.figure_folder = f'{os.environ["HOME"]}/Dropbox/Apps/Overleaf/väitöskirja/figures'
        self.design_sets = ["SBnight", "SBday", "SALSAnight", "SALSAday"]

        self.design_methods_with_R = ["scmc", "comined"]

        self.design_methods_python = ["ga", "bsp", "manuscript"]

        self.design_methods_all = self.design_methods_with_R + self.design_methods_python

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

        color_list = Colorful.getDistinctColorList(["green", "blue", "yellow", "orange", "red"])

        self.method_with_color = dict(zip(self.design_methods_all, color_list))

        marker_list = ["3", "4", "X", "^", "v"]

        self.method_with_marker = dict(zip(self.design_methods_all, marker_list))

        self.maximin_column_names = {}
        for dd_set in self.design_sets:
            self.maximin_column_names[dd_set] = []

        self.normalised_maximin_column_names = {}
        for dd_set in self.design_sets:
            self.normalised_maximin_column_names[dd_set] = []

        self.maximum_dict = dict(zip(self.design_sets, repeat(numpy.nan)))

        self.debug = False

        self.look = LookUpTable()

        self.annotationValues = ["(a) SB Night",
            "(b) SB Day",
            "(c) SALSA Night",
            "(d) SALSA Day"]

        self.design_sensible_names = dict(zip(self.design_sets, ["SB Night",
            "SB Day",
            "SALSA Night",
            "SALSA Day"]))

        self.annotationCollection = dict(zip(self.design_sets, self.annotationValues))

        self.annotationXPositions = dict(zip(self.design_sets, [0.57, 0.63, 0.45, 0.50 ]))


    def get_sensible_name(self, key):

        sensible_dict = {"scmc" : "SCMC",
                         "comined" : "CoMinED",
                         "bsp": "BSP",
                         "manuscript": "Paper III (BSP)"}

        return sensible_dict[key]

    def get_manuscript_results(self):
        manu_folder = os.environ["DESIGNRESULTSMANUSCRIPT"]
        manu_path_folder = pathlib.Path(manu_folder)

        for file_name in list(manu_path_folder.glob("**/*.csv")):
            design = pandas.read_csv(file_name, index_col=0)
            seeti = str(file_name.name).split(".")[0]
            hypercube_design = self.look.downscale_dataframe(design)
            maximin = MaximinDesign.matrix_minimum_distance(hypercube_design.values)

            print(maximin)

            design_points = design.shape[0]

            df = pandas.DataFrame(data=[maximin],
                                  index = [design_points],
                                  columns=["maximin_manuscript"])
            df.index.name = "design_points"

            df.to_csv(self.folder / seeti / ("manuscript_stats.csv"))

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
                if not stats_file.is_file() and method == "ga":
                    continue
                else:
                    assert stats_file.is_file(), stats_file

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
            self.joined_stats[dd_set].reset_index(inplace=True)


    def get_maximin_column_names(self):
        for dd_set in self.joined_stats:
            for column_name in self.joined_stats[dd_set].columns:
                splitted = column_name.split("_")
                if splitted[1] in  ["ga"]:
                    continue

                if splitted[0] == "maximin":
                    self.maximin_column_names[dd_set].append(column_name)

        if self.debug:
            for dd_set in self.design_sets:
                print(dd_set)
                for method_result in self.maximin_column_names[dd_set]:
                    print(f"{dd_set} {method_result} min: {numpy.log(self.joined_stats[dd_set][method_result].min()):.1f} max: {numpy.log(self.joined_stats[dd_set][method_result].max()):.1f}")


    def get_maximum_values_of_maximins(self):
        for dd_set in self.design_sets:
            for method_result in self.maximin_column_names[dd_set]:
                self.maximum_dict[dd_set] = numpy.nanmax([self.maximum_dict[dd_set],
                                                    self.joined_stats[dd_set][method_result].max()])

    def normalise_maximin_results_based_on_maximum(self):
        for dd_set in self.design_sets:
            for method_result in self.maximin_column_names[dd_set]:

                normalised_name = "normalised_" + method_result
                self.joined_stats[dd_set][normalised_name] = self.joined_stats[dd_set][method_result] / self.maximum_dict[dd_set]

                self.normalised_maximin_column_names[dd_set].append(normalised_name)

    def plot_results(self):
        self.figures["maximin"] = Figure(self.figure_folder,"maximin",
                                        figsize=[self.figure_width, 6],
                                        ncols=2,
                                        nrows=2,
                                        hspace=0.05, bottom=0.1, wspace = 0.05, top = 0.93)

        fig = self.figures["maximin"]
        for dd_ind, dd_set in enumerate(list(self.design_sets)):
            current_axis = fig.getAxes(dd_ind)

            for method_column in self.normalised_maximin_column_names[dd_set]:
                method_name = method_column.split("_")[-1]
                df = self.joined_stats[dd_set]
                df.plot(kind="scatter",
                        marker=self.method_with_marker[method_name],
                            x="design_points",
                            y=method_column,
                            ax = current_axis,
                            color = self.method_with_color[method_name],
                            legend = False,
                            s=40,
                            alpha=0.45
                            )

            if dd_ind in [1,3]:
                PlotTweak.hideYTickLabels(current_axis)

            if dd_ind in [0,1]:
                PlotTweak.hideXTickLabels(current_axis)


            PlotTweak.setYaxisLabel(current_axis,"")
            PlotTweak.setXaxisLabel(current_axis,"")

            if dd_ind == 3:
                current_axis.text(-175,0,
                                  "Number of design points", #PlotTweak.getLatexLabel(, ""),
                                  size=8)

            if dd_ind == 2:
                current_axis.text(PlotTweak.getXPosition(current_axis, -0.25), PlotTweak.getYPosition(current_axis, 0.2),
                        "Maximin measure relative to the highest measure within a set", size=8 , rotation =90)

            if dd_ind == 0:

                names = [key for key in self.method_with_color if key != "ga"]
                colors = [self.method_with_color[key] for key in names]
                sensible_names = [self.get_sensible_name(key) for key in names]

                sensible_names_with_color = dict(zip(sensible_names, colors))

                legendLabelColors = PlotTweak.getPatches(sensible_names_with_color)
                artist = current_axis.legend(handles=legendLabelColors,
                                             loc=(-0.02, 1.05),
                                             frameon=True,
                                             framealpha=0.8,
                                             ncol=len(list(self.method_with_color)))

                current_axis.add_artist(artist)

            PlotTweak.setAnnotation(current_axis,
                                    self.annotationCollection[dd_set],
                                    xPosition=PlotTweak.getXPosition(current_axis, self.annotationXPositions[dd_set]),
                                    yPosition=PlotTweak.getYPosition(current_axis, 0.93))



    def save_figures(self):

        for fig in self.figures.values():
            fig.save(file_extension = ".pdf")





def main():
    dd = DesignAnalysis()




    update_results = False

    if update_results:
        dd.get_manuscript_results()
        dd.get_maximin_results_with_R()
        dd.save_results_with_R()


    dd.read_all_results()
    dd.get_maximin_column_names()
    dd.reset_index()
    dd.sort_by_design_points()
    dd.get_maximum_values_of_maximins()
    dd.normalise_maximin_results_based_on_maximum()
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

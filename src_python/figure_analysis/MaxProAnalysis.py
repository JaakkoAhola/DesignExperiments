#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
import os
import numpy
import pathlib

from itertools import repeat
import pandas
from matplotlib.lines import Line2D

# package imports
from library import Data
from library import Colorful
from library import Figure
from library import FileSystem
from library import PlotTweak
from library import Metrics
from algorithms import LookUpTable

from dotenv import load_dotenv
load_dotenv()


class MaxProxAnalysis:

    def __init__(self,
                 folder=pathlib.Path(os.environ["REPO"]) /
                 "data/02_raw_output/design_stats_maxpro",
                 ):

        self.figure_folder = pathlib.Path(os.environ["REPO"]) / "data/03_figure_analysis"
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
        self.figure_width = 12 / 2.54

        color_list = Colorful.get_distinct_color_list_by_name(
            ["green", "blue", "yellow", "orange", "red"])

        marker_list = ["3", "4", "X", "^", "v"]

        self.method_with_marker = dict(zip(self.design_methods_all, marker_list))

        self.method_with_color = dict(zip(self.design_methods_all, color_list))

        self.maxpro_column_names = {}
        for dd_set in self.design_sets:
            self.maxpro_column_names[dd_set] = []

        self.normalised_maxpro_column_names = {}
        for dd_set in self.design_sets:
            self.normalised_maxpro_column_names[dd_set] = []

        self.maximum_dict = dict(zip(self.design_sets, repeat(numpy.nan)))

        self.debug = False

        self.look = LookUpTable.LookUpTable()
        self.look.load_look_up_tables()
        self.annotationValues = ["(a) SB Night",
                                 "(b) SB Day",
                                 "(c) SALSA Night",
                                 "(d) SALSA Day"]

        self.annotationCollection = dict(zip(self.design_sets, self.annotationValues))

        self.annotationXPositions = dict(zip(self.design_sets, [0.57, 0.63, 0.45, 0.50]))

    def get_sensible_name(self, key):

        sensible_dict = {"scmc": "SCMC",
                         "comined": "CoMinED",
                         "bsp": "BSP",
                         "manuscript": "Paper III (BSP)"}

        return sensible_dict[key]

    def get_manuscript_results(self):
        manu_path_folder = pathlib.Path(os.environ["REPO"]) / "data/01_source/manuscript_designs"
        list_of_designs = list(manu_path_folder.glob("**/*.csv"))
        assert len(list_of_designs) >= 0, \
            f"List of design points stats empty, check folder {manu_path_folder}"
        for file_name in list_of_designs:
            design = pandas.read_csv(file_name, index_col=0)
            seeti = str(file_name.name).split(".")[0]
            hypercube_design = self.look.downscale_dataframe(design)
            maxpro = Metrics.max_pro_measure(hypercube_design.values)

            print(maxpro)

            design_points = design.shape[0]

            df = pandas.DataFrame(data=[maxpro],
                                  index=[design_points],
                                  columns=["maxpro_manuscript"])
            df.index.name = "design_points"

            df.to_csv(self.folder / seeti / ("manuscript_stats.csv"))

    def get_maxpro_results_with_R(self):

        for dd_set in self.stats:
            for method in self.design_methods_with_R:
                subfolder = self.folder / dd_set / method
                list_of_designs = list(subfolder.glob("**/*.csv"))
                assert len(list_of_designs) >= 0, \
                    f"List of design points stats empty, check folder {dd_set}/{method}"
                for file_name in list_of_designs:
                    design_points = FileSystem.get_design_points_from_filename(file_name)
                    maxpro = Metrics.max_pro_measure(pandas.read_csv(file_name).values)
                    tupp = (design_points, maxpro)
                    self.stats[dd_set][method].append(tupp)

        for dd_set in self.design_sets:
            for method in self.design_methods_with_R:
                list_of_tuples = self.stats[dd_set][method]

                self.stats[dd_set][method] = pandas.DataFrame\
                    .from_records(list_of_tuples,
                                  columns=['design_points',
                                           'maxpro_' + method])

                self.stats[dd_set][method].set_index("design_points", inplace=True)

    def save_results_with_R(self):
        for dd_set in self.design_sets:
            for method in self.design_methods_with_R:
                stats_file = self.folder / dd_set / (method + "_stats.csv")
                self.stats[dd_set][method].to_csv(stats_file)

    def save_results_with_bsp(self):
        for dd_set in self.design_sets:
            subfolder = self.folder / dd_set / "bsp"
            list_of_designs = list(subfolder.glob("**/stats_bsp_*.csv"))
            # Create an empty DataFrame to store the merged data
            merged_df = pandas.DataFrame(columns=['design_points', 'maxpro_bsp', 'duration_bsp'])

            # Use glob to get a list

            # Loop through the CSV files and append their data to the merged DataFrame
            for file_name in list_of_designs:
                df = pandas.read_csv(file_name)
                merged_df = pandas.concat([merged_df, df], ignore_index=True)

            # Save the merged DataFrame to a new CSV file
            merged_df = merged_df.sort_values(by='design_points')
            merged_df.to_csv(self.folder / dd_set / 'bsp_stats.csv', index=False)

    def read_all_results(self):

        for dd_set in self.design_sets:
            for method in self.design_methods_all:
                stats_file = self.folder / dd_set / (method + "_stats.csv")
                if not stats_file.is_file() and method == "ga":
                    continue
                else:
                    assert stats_file.is_file(), stats_file

                df = pandas.read_csv(stats_file, index_col=0)

                if self.joined_stats[dd_set] is None:
                    self.joined_stats[dd_set] = df
                else:
                    self.joined_stats[dd_set] = df.merge(
                        self.joined_stats[dd_set], how="outer", on="design_points")

    def reset_index(self):
        for dd_set in self.design_sets:
            self.joined_stats[dd_set].reset_index(inplace=True)

    def sort_by_design_points(self):
        for dd_set in self.design_sets:
            self.joined_stats[dd_set].sort_values(by="design_points",
                                                  inplace=True)
            self.joined_stats[dd_set].reset_index(inplace=True)

    def get_maxpro_column_names(self):
        for dd_set in self.joined_stats:
            for column_name in self.joined_stats[dd_set].columns:
                splitted = column_name.split("_")
                if splitted[1] in ["ga"]:
                    continue

                if splitted[0] == "maxpro":
                    self.maxpro_column_names[dd_set].append(column_name)

        if self.debug:
            for dd_set in self.design_sets:
                print(dd_set)
                for method_result in self.maxpro_column_names[dd_set]:
                    print(
                        f"{dd_set} {method_result} min: {numpy.log(self.joined_stats[dd_set][method_result].min()):.1f} max: {numpy.log(self.joined_stats[dd_set][method_result].max()):.1f}")

    def get_maximum_values_of_maxpros(self):
        for dd_set in self.design_sets:
            for method_result in self.maxpro_column_names[dd_set]:
                self.maximum_dict[dd_set] = numpy.nanmax([self.maximum_dict[dd_set],
                                                          numpy.ma.masked_invalid(self.joined_stats[dd_set][method_result]).max()])

    def normalise_maxpro_results_based_on_maximum(self):
        for dd_set in self.design_sets:
            for method_result in self.maxpro_column_names[dd_set]:

                normalised_name = "normalised_" + method_result
                self.joined_stats[dd_set][normalised_name] = self.joined_stats[dd_set][method_result] / \
                    self.maximum_dict[dd_set]

                self.normalised_maxpro_column_names[dd_set].append(normalised_name)

    def plot_results(self):
        self.figures["maxpro"] = Figure.Figure(self.figure_folder, "maxpro",
                                               figsize=[self.figure_width, 6],
                                               ncols=2,
                                               nrows=2,
                                               hspace=0.06, bottom=0.1, wspace=0.07, top=0.93)

        fig = self.figures["maxpro"]

        xstart = 0
        xend = 500
        xticks = numpy.arange(xstart, xend + 1, 50)
        xtickLabels = [f"{t:.0f}" for t in xticks]
        xshowList = Data.cycleBoolean(len(xticks))
        xshowList[0] = False

        ystart = 0
        yend = 1.0
        yticks = numpy.arange(ystart, yend + 0.1, 0.1)
        ytickLabels = [f"{t:.1f}" for t in yticks]

        yshowList = Data.cycleBoolean(len(yticks))
        yshowList[0] = False

        for dd_ind, dd_set in enumerate(list(self.design_sets)):
            current_axis = fig.getAxes(dd_ind)

            for method_column in self.normalised_maxpro_column_names[dd_set]:
                method_name = method_column.split("_")[-1]
                df = self.joined_stats[dd_set]
                df.plot(kind="scatter",
                        marker=self.method_with_marker[method_name],
                        x="design_points",
                        y=method_column,
                        ax=current_axis,
                        color=self.method_with_color[method_name],
                        legend=False,
                        alpha=0.45,
                        s=40
                        )

            PlotTweak.setXaxisLabel(current_axis, "")
            current_axis.set_xlim([xstart, xend + 20])
            current_axis.set_xticks(xticks)
            current_axis.set_xticklabels(xtickLabels)
            PlotTweak.hideLabels(current_axis.xaxis, xshowList)
            PlotTweak.setXTickSizes(current_axis, Data.cycleBoolean(len(xticks)))

            PlotTweak.setYaxisLabel(current_axis, "")
            current_axis.set_ylim([ystart, yend + 0.03])
            current_axis.set_yticks(yticks)
            current_axis.set_yticklabels(ytickLabels)
            PlotTweak.hideLabels(current_axis.yaxis, yshowList)
            PlotTweak.setYTickSizes(current_axis, Data.cycleBoolean(len(yticks)))

            if dd_ind in [1, 3]:
                PlotTweak.hideYTickLabels(current_axis)

            if dd_ind in [0, 1]:
                PlotTweak.hideXTickLabels(current_axis)

            if dd_ind == 3:
                current_axis.text(-175, -0.2,
                                  "Number of design points",  # PlotTweak.getLatexLabel(, ""),
                                  size=8)
            if dd_ind == 2:
                current_axis.text(PlotTweak.getXPosition(current_axis, -0.25), PlotTweak.getYPosition(current_axis, 0.2),
                                  "Maxpro measure relative to the highest measure within a set", size=8, rotation=90)

            if dd_ind == 0:

                names = [key for key in self.method_with_color if key != "ga"]

                legendLabelColors = []
                for key in names:
                    color = self.method_with_color[key]
                    sensible_name = self.get_sensible_name(key)
                    marker = self.method_with_marker[key]
                    legendLabelColors.append(Line2D([], [],
                                                    color=color,
                                                    linewidth=0,
                                                    marker=marker,
                                                    label=sensible_name,
                                                    markerfacecolor=color,
                                                    markersize=8,
                                                    alpha=0.45))

                artist = current_axis.legend(handles=legendLabelColors,
                                             loc=(-0.02, 1.05),
                                             frameon=True,
                                             framealpha=0.8,
                                             ncol=len(list(self.method_with_color)))

                current_axis.add_artist(artist)

            PlotTweak.setAnnotation(current_axis,
                                    self.annotationCollection[dd_set],
                                    xPosition=PlotTweak.getXPosition(
                                        current_axis, self.annotationXPositions[dd_set]),
                                    yPosition=PlotTweak.getYPosition(current_axis, 0.83))

    def save_figures(self):

        for fig in self.figures.values():
            fig.save(file_extension=os.environ["FIGEXTENSION"])

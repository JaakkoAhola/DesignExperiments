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
import pandas


# package imports
from library import Data
from library import Figure
from library import PlotTweak

from figure_analysis import MaximinAnalysis
from matplotlib.lines import Line2D


class FillDistanceAnalysis(MaximinAnalysis):
    def __init__(self,
                 folder=pathlib.Path(os.environ["REPO"]) /
                 "data/02_raw_output/design_stats_maximin",
                 postfix="maximin"):
        super().__init__(folder)
        self.postfix = postfix

    def read_all_results(self):
        for dd_set in self.design_sets:
            stats_file = self.folder / dd_set / ("filldistance_stats_" + dd_set + ".csv")

            df = pandas.read_csv(stats_file, index_col=0)

            if self.joined_stats[dd_set] is None:
                self.joined_stats[dd_set] = df
            else:
                self.joined_stats[dd_set] = df.merge(self.joined_stats[dd_set],
                                                     how="outer",
                                                     on="design_points")

    def get_maximin_column_names(self):
        for dd_set in self.joined_stats:
            for column_name in self.joined_stats[dd_set].columns:
                splitted = column_name.split("_")
                if splitted[1] in ["ga"]:
                    continue

                if splitted[0] == "filldistance":
                    self.maximin_column_names[dd_set].append(column_name)

    def plot_results(self):
        self.figures["filldistance"] = Figure.Figure(self.figure_folder, "filldistance_" + self.postfix,
                                                     figsize=[self.figure_width, 6],
                                                     ncols=2, nrows=2,
                                                     left=0.15, right=0.97,
                                                     hspace=0.06, bottom=0.1, wspace=0.07, top=0.93)

        fig = self.figures["filldistance"]

        xstart = 0
        xend = 500
        xticks = numpy.arange(xstart, xend + 1, 50)
        xtickLabels = [f"{t:.0f}" for t in xticks]
        xshowList = Data.cycleBoolean(len(xticks))
        xshowList[0] = False

        ystart = 1.90
        yend = 2.55
        yticks = numpy.arange(ystart, yend + 0.1, 0.05)
        ytickLabels = [f"{t:.1f}" for t in yticks]

        yshowList = Data.cycleBoolean(len(yticks))
        yshowList[0] = False
        maxi = -numpy.inf
        mini = numpy.inf

        for dd_ind, dd_set in enumerate(list(self.design_sets)):
            current_axis = fig.getAxes(dd_ind)

            for method_column in self.maximin_column_names[dd_set]:
                method_name = method_column.split("_")[-1]
                df = self.joined_stats[dd_set]
                maxi = max(maxi, df[method_column].max())
                mini = min(mini, df[method_column].min())

                df.plot(kind="scatter",
                        marker=self.method_with_marker[method_name],
                        x="design_points",
                        y=method_column,
                        ax=current_axis,
                        color=self.method_with_color[method_name],
                        legend=False,
                        s=40,
                        alpha=0.45
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

            PlotTweak.setYaxisLabel(current_axis, "")
            PlotTweak.setXaxisLabel(current_axis, "")

            if dd_ind == 3:
                current_axis.text(-175, PlotTweak.getYPosition(current_axis, -0.19),
                                  "Number of design points",
                                  size=8)

            if dd_ind == 2:
                current_axis.text(PlotTweak.getXPosition(current_axis, -0.32), PlotTweak.getYPosition(current_axis, 0.2),
                                  "Fill Distance measure with designs optimised with " + self.postfix, size=8, rotation=90)

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
                                    xPosition=PlotTweak.getXPosition(current_axis, 0.05),
                                    yPosition=PlotTweak.getYPosition(current_axis, 0.93))
        print("min", mini, "max", maxi)

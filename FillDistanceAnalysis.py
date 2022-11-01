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
from datetime import datetime
import pandas

sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data
from Colorful import Colorful
from Figure import Figure
from PlotTweak import PlotTweak

from DesignAnalysis import DesignAnalysis


class FillDistanceAnalysis(DesignAnalysis):
    def __init__(self,
                 folder=os.environ["DESIGNRESULTSMAXIMIN"],
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
        self.figures["filldistance"] = Figure(self.figure_folder, "filldistance_" + self.postfix,
                                              figsize=[self.figure_width, 6],
                                              ncols=2, nrows=2,
                                              hspace=0.05, wspace=0.05,
                                              left=0.15, right=0.97,
                                              bottom=0.1, top=0.93)

        fig = self.figures["filldistance"]
        for dd_ind, dd_set in enumerate(list(self.design_sets)):
            current_axis = fig.getAxes(dd_ind)

            for method_column in self.maximin_column_names[dd_set]:
                method_name = method_column.split("_")[-1]
                df = self.joined_stats[dd_set]
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

            if dd_ind in [1, 3]:
                PlotTweak.hideYTickLabels(current_axis)

            if dd_ind in [0, 1]:
                PlotTweak.hideXTickLabels(current_axis)

            PlotTweak.setYaxisLabel(current_axis, "")
            PlotTweak.setXaxisLabel(current_axis, "")

            if dd_ind == 3:
                current_axis.text(PlotTweak.getXPosition(current_axis, -0.5), PlotTweak.getYPosition(current_axis, -0.2),
                                  "Number of design points",
                                  size=8)

            if dd_ind == 2:
                current_axis.text(PlotTweak.getXPosition(current_axis, -0.32), PlotTweak.getYPosition(current_axis, 0.2),
                                  "Fill Distance measure with designs optimised with " + self.postfix, size=8, rotation=90)

            if dd_ind == 0:

                names = [key for key in self.method_with_color if key != "ga"]
                colors = [self.method_with_color[key] for key in names]
                sensible_names = [self.get_sensible_name(key) for key in names]

                sensible_names_with_color = dict(zip(sensible_names, colors))

                legendLabelColors = PlotTweak.getPatches(sensible_names_with_color)
                artist = current_axis.legend(handles=legendLabelColors,
                                             loc=(-0.1, 1.05),
                                             frameon=True,
                                             framealpha=0.8,
                                             ncol=len(list(self.method_with_color)))

                current_axis.add_artist(artist)

            PlotTweak.setAnnotation(current_axis,
                                    self.annotationCollection[dd_set],
                                    xPosition=PlotTweak.getXPosition(current_axis, self.annotationXPositions[dd_set]),
                                    yPosition=PlotTweak.getYPosition(current_axis, 0.93))


def main():
    optim_methods = {"maximin": os.environ["DESIGNRESULTSMAXIMIN"],
                     "maxpro": os.environ["DESIGNRESULTSMAXPRO"]}
    for key in optim_methods:
        fill = FillDistanceAnalysis(optim_methods[key],
                                    key)
        fill.read_all_results()
        fill.get_maximin_column_names()
        fill.reset_index()
        fill.plot_results()
        fill.save_figures()


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")

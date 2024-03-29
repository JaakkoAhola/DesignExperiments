#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 19.1.2022

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""

import os
import re
import pandas
import pathlib
from math import ceil
import numpy
import matplotlib
import matplotlib.ticker as mticker
from copy import deepcopy

# package imports
from library import Data
from library import Colorful
from library import Figure
from library import PlotTweak
from figure_analysis import MaximinAnalysis

from dotenv import load_dotenv
load_dotenv()


class DistributionAnalysis(MaximinAnalysis.MaximinAnalysis):
    def __init__(self,
                 folder=pathlib.Path(os.environ["REPO"]) /
                 "data/02_raw_output/design_stats_maximin",
                 postfix="maximin",
                 debug=False):

        super().__init__(folder)
        self.postfix = postfix

        self.debug = debug

        self._initDesignVariables()

        self.design_methods_all.remove("ga")

        self.method_sensible_names = [self.get_sensible_name_legend(
            key) for key in self.design_methods_all]

        self.method_sensible_names_dict = dict(
            zip(self.design_methods_all, self.method_sensible_names))

        self.method_sensible_names_with_color = {}
        for key in self.design_methods_all:
            sensible_name = self.method_sensible_names_dict[key]
            color = self.method_with_color[key]
            self.method_sensible_names_with_color[sensible_name] = color

        self.allSetColors = deepcopy(self.method_sensible_names_with_color)
        self.allSetColors["Filtered ECHAM"] = Colorful.get_distinct_color_list_by_name("grey")

        self.trainingetSetsForVariables = {}
        for key in self.designVariablePool:
            if (key in self.meteorologicalVariables + self.microphysicsVariablesPool["SB"] + self.solarZenithAngle):
                self.trainingetSetsForVariables[key] = "SBday"
            elif (key in self.microphysicsVariablesPool["SALSA"]):
                self.trainingetSetsForVariables[key] = "SALSAday"

    def get_sensible_name_legend(self, key):

        sensible_dict = {"scmc": "SCMC",
                         "comined": "CoMinED",
                         "bsp": "BSP",
                         "manuscript": "Paper III (BSP)"}

        return sensible_dict[key]

    def _initDesignVariables(self):
        self.meteorologicalVariables = ["tpot_pbl", "tpot_inv", "q_inv", "lwp", "pbl", ]
        self.microphysicsVariablesPool = {"SB": ["cdnc"],
                                          "SALSA": ["ks", "as", "cs", "rdry_AS_eff"]}
        self.solarZenithAngle = ["cos_mu"]
        self.designVariablePool = self.meteorologicalVariables + \
            [item for sublist in list(self.microphysicsVariablesPool.values())
             for item in sublist] + self.solarZenithAngle

    def initReadFilteredSourceData(self):
        localPath = pathlib.Path(os.environ["REPO"])

        if not self.debug:

            self.filteredSourceData = pandas.read_csv(
                localPath / "data/01_source/eclair_dataset_2001_designvariables.csv",
                index_col=0)
        else:

            self.filteredSourceData = pandas.read_csv(
                localPath / "data/01_source/sample20000.csv",
                index_col=0)

    def read_all_designs(self):
        print("read_all_designs")
        skip_pattern = r'stats_bsp_\d+\.csv'
        for trainingSet in self.design_sets:
            for method in self.design_methods_all:
                subfolder = self.folder / trainingSet / method
                self.stats[trainingSet][method] = {}
                list_of_designs = list(subfolder.glob("**/*.csv"))
                assert len(list_of_designs) >= 0, \
                    f"List of design points stats empty, check folder {trainingSet}/{method}"

                for file_name in list_of_designs:
                    if re.match(skip_pattern, file_name.name):
                        continue
                    df = pandas.read_csv(file_name, index_col=0)

                    if method not in ["manuscript", "bsp"]:
                        df = self.look.upscale_dataframe(df)
                    design_points = len(df)
                    print(trainingSet, method, design_points, file_name)
                    self.stats[trainingSet][method][design_points] = df

                    print(self.stats[trainingSet][method])
        print("-- exiting")

    def figure_design_variable_distribution(self):
        nrows = 4
        ncols = ceil(len(self.designVariablePool) / nrows)
        name = "figure_design_variable_distribution_" + self.postfix
        self.figures[name] = Figure.Figure(self.figure_folder,
                                           name,
                                           figsize=[self.figure_width, 7],
                                           ncols=ncols, nrows=nrows,
                                           bottom=0.04, top=0.98,
                                           hspace=0.17, wspace=0.07,
                                           left=0.05, right=0.99)

        fig = self.figures[name]
        default = [0.02, 0.02]
        rightUp = [0.57, 0.70]
        leftUp = [0.25, 0.73]
        leftDown = [0.1, 0]
        rightDown = [0.45, 0.05]
        middleDown = [0.33, 0.05]
        default = [0.5, 0.5]
        specsPositions = [[0.3, 0.05], [0.2, 0.05], [0.3, 0.5],
                          [0.3, 0.5], [0.3, 0.05], [0.3, 0.5],
                          [0.3, 0.5], [0.3, 0.5], [0.3, 0.5],
                          middleDown, middleDown
                          ]

        aeroNumberVariables = ["ks", "as", "cs"]
        reff = "rdry_AS_eff"

        minisDesigns = [numpy.nan] * len(self.designVariablePool)
        maxisDesigns = [numpy.nan] * len(self.designVariablePool)

        for ind, variable in enumerate(self.designVariablePool):
            trainingSet = self.trainingetSetsForVariables[variable]
            ax = fig.getAxes(ind)

            minimi = numpy.nan
            maximi = numpy.nan

            variableSourceName = variable

            if hasattr(self, "filteredSourceData") and (self.filteredSourceData is not None):
                sourceDataVariable = self.filteredSourceData[variableSourceName]
                sourceDataVariable = Data.dropInfNanFromDataFrame(sourceDataVariable)
                if variable in aeroNumberVariables:
                    sourceDataVariable = sourceDataVariable * 1e-6
                if variable == reff:
                    sourceDataVariable = sourceDataVariable * 1e9
                sourceDataVariable = Data.dropInfNanFromDataFrame(sourceDataVariable)

                if variable == "cos_mu":
                    sourceDataVariable = sourceDataVariable[sourceDataVariable > Data.getEpsilon()]
                sourceDataVariable.plot.density(ax=ax,
                                                color=Colorful.get_distinct_color_list_by_name("grey"))

                if variable in (aeroNumberVariables + [reff, "cdnc"]):
                    print(
                        f"{variable} ECHAM mean {sourceDataVariable.mean():.2f}, ECHAM median {sourceDataVariable.median():.2f}")

            for method in self.design_methods_all:
                if method == "manuscript" and variable == "pbl":
                    variable = "pblh"
                print("design maximi", trainingSet, method,
                      self.stats[trainingSet][method].keys())
                design_points = max(self.stats[trainingSet][method].keys())

                try:
                    trainingSetVariable = self.stats[trainingSet][method][design_points][variable]
                except KeyError:
                    print(
                        f"KeyError, training set: {trainingSet}, method: {method}, design_points: {design_points}, variable: {variable}")
                    continue

                if variable in aeroNumberVariables:
                    trainingSetVariable = trainingSetVariable * 1e-6
                if variable == reff:
                    trainingSetVariable = trainingSetVariable * 1e9

                trainingSetVariable = Data.dropInfNanFromDataFrame(trainingSetVariable)

                minimi = numpy.nanmin([minimi, trainingSetVariable.min()])
                maximi = numpy.nanmax([maximi, trainingSetVariable.max()])

                minisDesigns[ind] = minimi
                maxisDesigns[ind] = maximi
                trainingSetVariable.plot.density(ax=ax,
                                                 color=self.method_with_color[method])

                if variable in (aeroNumberVariables + [reff, "cdnc"]):
                    print(
                        f"{variable} {trainingSet} mean {trainingSetVariable.mean():.2f} {trainingSet} median {trainingSetVariable.median():.2f}")

            variableAnnotationYposition = 0.9

            if variable == "cos_mu":
                annotationOfVariable = PlotTweak.getMathLabel(variable)

            else:
                annotationOfVariable = PlotTweak.getUnitLabel(
                    PlotTweak.getMathLabelFromDict(variable), PlotTweak.getVariableUnit(variable))

            annotation = f"({Data.getNthLetter(ind)}) {annotationOfVariable}"
            PlotTweak.setAnnotation(ax, annotation,
                                    xPosition=0.02,
                                    yPosition=0.91,
                                    xycoords="axes fraction")

            ax.set_ylabel("")

            ax.set_ylim([0, ax.get_ylim()[1]])

            # fixing yticks with matplotlib.ticker "FixedLocator"
            label_format = '{:,.0f}'
            ticks_loc = ax.get_yticks().tolist()
            ax.yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
            yticklabels = [label_format.format(x) for x in ticks_loc]
            yticklabels[0] = "0"
            ax.set_yticklabels(yticklabels)

            if ind in [0, 3, 6, 9, 12]:
                matplotlib.pyplot.setp(ax.get_yticklabels()[0], visible=True)
                matplotlib.pyplot.setp(ax.get_yticklabels()[1:], visible=False)
            else:
                PlotTweak.hideYTickLabels(ax)

            try:
                ax.set_xlim([minimi, maximi])
            except ValueError:
                continue

        ax = fig.getAxes(11)
        ax.axis("off")

        legendLabelColors = PlotTweak.getPatches(self.allSetColors)

        artist = ax.legend(handles=legendLabelColors, loc=(
            0.0, 0.00), frameon=True, framealpha=1.0, ncol=1)

        ax.add_artist(artist)

        for ind, variable in enumerate(self.designVariablePool):
            ax = fig.getAxes(ind)
            trainingSet = self.trainingetSetsForVariables[variable]

            variableSpecs = f"""{PlotTweak.getLatexLabel(f'min={minisDesigns[ind]:.2f}')}
{PlotTweak.getLatexLabel(f'max={maxisDesigns[ind]:.2f}')}
"""

            ax.annotate(variableSpecs,
                        xy=specsPositions[ind],
                        size=4,
                        bbox=dict(pad=0.6, fc="w", ec="w", alpha=0.9), xycoords="axes fraction")

            if ind in [1, 2, 3]:
                ax.set_xlim([0, maxisDesigns[ind]])
            if ind in [5, 6, 7, 8]:
                limits = {5: 200, 6: 1000, 7: 300, 8: 15}
                ax.set_xlim([0, limits[ind]])
                matplotlib.pyplot.setp(ax.get_xticklabels()[-1], visible=False)
            if ind == 10:
                ax.set_xlim([0, 1])
                label_format = '{:,.2f}'
                ticks_loc = ax.get_xticks().tolist()
                ax.xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
                xticklabels = [label_format.format(x) for x in ticks_loc]
                xticklabels[0] = "0"
                xticklabels[-1] = "1"
                ax.set_xticklabels(xticklabels)

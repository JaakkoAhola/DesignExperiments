#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 18:42:33 2021

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
import math
import os
import pathlib
from itertools import repeat
from itertools import combinations

# 3rd party imports
import numpy
import pandas
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV

# package imports
from library import Data
from library import Colorful
from library import Figure
from library import PlotTweak
from libray import FileSystem

from dotenv import load_dotenv
load_dotenv()


def my_scores(estimator, x):
    scores = estimator.score_samples(x)
    # Remove -inf
    scores = scores[scores != float('-inf')]
    # Return the mean values
    return numpy.mean(scores)


def filter_out_zeros(parameter_at_hand):
    condition = parameter_at_hand > Data.getEpsilon()
    parameter_at_hand = parameter_at_hand[condition]

    return parameter_at_hand


class SourceVsSampleVsDesignAnalysis():

    def __init__(
        self,
        yaml_config_file=pathlib.Path(os.environ["REPO"]) /
        "input_yaml/all_but_source_updated_lhs.yaml",
        figure_folder=pathlib.Path(os.environ["REPO"]) / + "data/03_figure_analysis/lhs/figures"
    ):

        self.yaml_config_file = FileSystem.readYAML(yaml_config_file)

        self.files = {}
        self.colors = {}
        for key in self.yaml_config_file:
            self.files[key] = pathlib.Path(self.yaml_config_file[key]["file"])
            self.colors[key] = Colorful.get_distinct_color_list_by_name(self.yaml_config_file[key]["color"])

        self.dataframes = {}

        self.figure_folder = pathlib.Path(figure_folder)

        self.figure_folder.mkdir(parents=True, exist_ok=True)

        self.figures = {}

        self.figure_width = 12 / 2.54

        self.parameters = sorted(['tpot_pbl',
                                  'tpot_inv',
                                  'q_inv',
                                  'lwp',
                                  'pbl',
                                  'cdnc',
                                  'ks',
                                  'as',
                                  'cs',
                                  'rdry_AS_eff',
                                  'cos_mu'])
        self.kernels = {}

        self._read_dataframes()
        self._unit_transform_dataframes()

    def _read_dataframes(self):
        for key in self.files:
            self.dataframes[key] = pandas.read_csv(self.files[key],
                                                   index_col=0)

    def get_source(self):
        return self.dataframes["source"]

    def get_sample(self):
        return self.dataframes["sample"]

    def get_lhs_sample(self):
        return self.dataframes["lhs"]

    def create_sample(self, sample_n=1000):
        assert "source" in self.dataframes
        self.dataframes["sample"] = self.dataframes["source"].sample(n=sample_n,
                                                                     random_state=0)

    def write_sample(self):
        assert "sample" in self.dataframes
        self.dataframes["sample"].to_csv(self.files["sample"])

    def _unit_transform_dataframes(self):
        factor = {'q_inv': 1,
                  'tpot_inv': 1,
                  'lwp': 1,
                  'tpot_pbl': 1,
                  'pbl': 1,
                  'cdnc': 1,
                  'ks': 1e-6,
                  'as': 1e-6,
                  'cs': 1e-6,
                  'rdry_AS_eff': 1e9,
                  'cos_mu': 1}

        for dataframe_name in self.dataframes:
            dataframe = self.dataframes[dataframe_name]
            for feature in dataframe.keys():
                if feature in factor:
                    dataframe[feature] = dataframe[feature] * factor[feature]

    def _init_kernel_search(self):
        kernels_base = ['cosine', 'gaussian', 'linear', 'tophat']

        self.kernels = dict(zip(self.parameters, repeat(["tophat"])))

        self.kernels["pbl"] = kernels_base
        self.kernels["cdnc"] = kernels_base
        self.kernels["ks"] = kernels_base
        self.kernels["as"] = kernels_base
        self.kernels["cs"] = kernels_base
        self.kernels["rdry_AS_eff"] = kernels_base

    def finalise_figures(self):
        for key in self.figures:
            self.figures[key].save()

    def _figure_final_tweaks_with_all_parameters(self, figure_name):

        self._figure_generalised_tweaks(figure_name)
        self._figure_get_mins_and_max(figure_name)

    def _figure_object_with_all_parameters(self, figure_name):
        ncols = 3
        nrows = math.ceil(len(self.parameters) / ncols)

        self.figures[figure_name] = Figure.Figure(self.figure_folder,
                                                  figure_name,
                                                  figsize=[self.figure_width, 7],
                                                  ncols=ncols,
                                                  nrows=nrows,
                                                  bottom=0.04,
                                                  hspace=0.17,
                                                  wspace=0.07,
                                                  top=0.98,
                                                  left=0.05,
                                                  right=0.99)

        current_ax = self.figures[figure_name].getAxes(ncols * nrows - 1)
        current_ax.axis("off")

        return self.figures[figure_name]

    def _figure_get_mins_and_max(self, figure_name):

        fig = self.figures[figure_name]

        for ind, parameter_name in enumerate(self.parameters):
            current_ax = fig.getAxes(ind)

            minimi = numpy.nan
            maximi = numpy.nan

            for key in self.dataframes:
                dataframe_at_hand = self.dataframes[key]

                try:
                    parameter_at_hand = dataframe_at_hand[parameter_name]
                except KeyError:
                    continue

                minimi = numpy.nanmin([minimi, parameter_at_hand.min()])

                maximi = numpy.nanmax([maximi, parameter_at_hand.max()])

            current_ax.set_xlim([minimi, maximi])
            current_ax.set_ylim([0, current_ax.get_ylim()[1]])

    def _figure_generalised_tweaks(self, figure_name):
        fig = self.figures[figure_name]

        for ind, parameter_name in enumerate(self.parameters):
            current_ax = fig.getAxes(ind)

            current_ax.set_ylabel("")
            PlotTweak.hideYTickLabels(current_ax)

            variable_annotation_y_position = 0.9
            if parameter_name == "pbl":
                plot_param_name = "pblh"
            else:
                plot_param_name = parameter_name

            if parameter_name == "cos_mu":
                annotation_of_variable = PlotTweak.getMathLabel(plot_param_name)

            else:
                math_label = PlotTweak.getMathLabelFromDict(plot_param_name)
                unit_label = PlotTweak.getVariableUnit(plot_param_name)
                annotation_of_variable = PlotTweak.getUnitLabel(math_label,
                                                                unit_label)

            annotation = f"({Data.getNthLetter(ind)}) {annotation_of_variable}"
            PlotTweak.setAnnotation(current_ax, annotation,
                                    xPosition=0.2,
                                    yPosition=variable_annotation_y_position,
                                    xycoords="axes fraction")

    def figure_source_vs_sample_vs_designs_kde_plot(self):
        name = "figure_source_vs_sample_vs_designs_kde_plot"
        fig = self._figure_object_with_all_parameters(name)

        self._init_kernel_search()
        h_vals = numpy.arange(0.05, 1, .1)

        for ind, parameter_name in enumerate(self.parameters):
            current_ax = fig.getAxes(ind)

            for key in self.dataframes:
                dataframe_at_hand = self.dataframes[key]

                try:
                    parameter_at_hand = dataframe_at_hand[parameter_name]
                except KeyError:
                    continue

                if parameter_name == "cos_mu":
                    parameter_at_hand = filter_out_zeros(parameter_at_hand)

                x_train = parameter_at_hand.values.reshape(-1, 1)

                grid = GridSearchCV(KernelDensity(),
                                    {'bandwidth': h_vals,
                                     'kernel': self.kernels[parameter_name]},
                                    scoring=my_scores)

                grid.fit(x_train)
                best_kde = grid.best_estimator_

                x_test = numpy.linspace(x_train.min(),
                                        x_train.max(),
                                        2000)[:, numpy.newaxis]
                log_dens = best_kde.score_samples(x_test)
                current_ax.plot(x_test,
                                numpy.exp(log_dens),
                                c=self.colors[key])

                title = f"Best Kernel: {best_kde.kernel} \
                        h= {best_kde.bandwidth:.2f}"

                print(parameter_name, title)
                current_ax.set_title(title)

        self._figure_final_tweaks_with_all_parameters(name)

    def figure_source_vs_sample_vs_designs_bar_plot(self):
        name = "figure_source_vs_sample_vs_designs_bar_plot"
        fig = self._figure_object_with_all_parameters(name)

        for ind, parameter_name in enumerate(self.parameters):
            current_ax = fig.getAxes(ind)

            for key in self.dataframes:
                dataframe_at_hand = self.dataframes[key]

                try:
                    parameter_at_hand = dataframe_at_hand[parameter_name]
                except KeyError:
                    continue

                if parameter_name == "cos_mu":
                    parameter_at_hand = filter_out_zeros(parameter_at_hand)

                parameter_at_hand.plot.density(
                    ax=current_ax,
                    color=self.colors[key])

        self._figure_final_tweaks_with_all_parameters(name)

    def figure_scatter_plot_projections(self):

        blue = Colorful.get_distinct_color_list_by_name("blue")
        red = Colorful.get_distinct_color_list_by_name("red")

        for key in self.dataframes:
            dataframe_at_hand = self.dataframes[key]

            if "q_constraint" in dataframe_at_hand.keys():
                dataframe_at_hand["color"] = dataframe_at_hand.apply(lambda row:
                                                                     blue if row["q_constraint"] else red, axis=1)
            else:
                dataframe_at_hand["color"] = blue

            subset_keys = set(dataframe_at_hand.keys())
            all_keys = set(self.parameters)

            parameters_at_hand = sorted(list(subset_keys & all_keys))

            ncols = len(parameters_at_hand)
            nrows = len(parameters_at_hand)

            combs = list(combinations(parameters_at_hand, 2))

            plot_matrix_boolean = numpy.array(numpy.zeros((nrows, ncols)), dtype='bool')
            figure_name = f"figure_scatter_plot_projections_{key}"
            self.figures[figure_name] = Figure.Figure(self.figure_folder,
                                                      figure_name,
                                                      figsize=[ncols * 2, nrows * 2],
                                                      ncols=ncols,
                                                      nrows=nrows,
                                                      bottom=0.04,
                                                      hspace=0.37,
                                                      wspace=0.07,
                                                      top=0.98,
                                                      left=0.05,
                                                      right=0.99)

            fig = self.figures[figure_name]

            for ind_comb, comb_value in enumerate(combs):

                abscissa = comb_value[0]
                oordinaatta = comb_value[1]

                ind_abscissa = parameters_at_hand.index(abscissa)
                ind_oordinaatta = parameters_at_hand.index(oordinaatta)

                current_ax = fig.getAxesGridPoint({"row": ind_oordinaatta,
                                                   "col": ind_abscissa})

                try:
                    dataframe_at_hand.plot.scatter(ax=current_ax,
                                                   x=abscissa,
                                                   y=oordinaatta,
                                                   s=2,
                                                   c="color")
                    plot_matrix_boolean[ind_oordinaatta, ind_abscissa] = True
                except KeyError:
                    continue
            for row in range(nrows):
                for col in range(ncols):
                    current_ax = fig.getAxesGridPoint({"row": row,
                                                       "col": col})
                    if not plot_matrix_boolean[row, col]:
                        current_ax.axis("off")
                    if col > 0:
                        current_ax.set_ylabel("")
                        PlotTweak.hideYTickLabels(current_ax)

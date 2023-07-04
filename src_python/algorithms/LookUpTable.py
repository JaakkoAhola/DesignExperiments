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

import pathlib
import pandas
import numpy
from datetime import datetime
from copy import deepcopy
from bisect import bisect_right

sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data
from itertools import repeat
from sklearn.linear_model import LinearRegression


class LookUpTable:

    def __init__(self, debug=False):
        self.all_variables = ["q_inv", "tpot_inv", "lwp", "tpot_pbl",
                              "pbl", "cdnc", "ks", "as", "cs", "rdry_AS_eff", "cos_mu"]
        self.datarootfolder = pathlib.Path(os.environ["DATAT"])
        self.mainfolder = self.datarootfolder / "ECLAIR"
        if debug:
            self.collection_filename = self.mainfolder / "sample20000.csv"
        else:
            self.collection_filename = self.mainfolder / "eclair_dataset_2001_designvariables.csv"

        self.collection_dataframe = None

        self.look_up_tables = dict(zip(self.all_variables, repeat(None)))

        self.__init__wrapper()

    def __init__wrapper(self):
        self.create_look_up_tables()
        self.load_look_up_tables()

    def load_collection(self):
        self.collection_dataframe = pandas.read_csv(self.collection_filename, index_col=0)

        return self.collection_dataframe

    def get_collection_dataframe(self):
        return self.collection_dataframe

    def create_look_up_tables(self):
        for key in self.all_variables:
            file = self.mainfolder / (self.collection_filename.stem +
                                      "_look_up_table_" + key + ".csv")
            if file.is_file():
                next
            else:
                if self.collection_dataframe is None:
                    self.load_collection()

                if (key in ["cos_mu", "rdry_AS_eff"]):
                    filtered_data = deepcopy(
                        self.collection_dataframe[self.collection_dataframe[key] > Data.getEpsilon()])

                else:
                    filtered_data = deepcopy(self.collection_dataframe)

                sorted_dataframe = filtered_data.sort_values(key)
                sorted_series = sorted_dataframe[key]
                sorted_series.reset_index(inplace=True, drop=True)

                sorted_series.to_csv(file)

    def load_look_up_tables(self):
        for key in self.all_variables:
            file = self.mainfolder / (self.collection_filename.stem +
                                      "_look_up_table_" + key + ".csv")
            assert file.is_file()

            df = pandas.read_csv(file)

            if df.shape[1] == 2:
                df = pandas.read_csv(file, index_col=0)

            self.look_up_tables[key] = df

    def function_look_up_table(self, key, value_within_unit_hyper_cube):
        look_up_table = self.look_up_tables[key]
        samples_in_look_up_table = look_up_table.shape[0]
        xth_point = int(round(value_within_unit_hyper_cube * samples_in_look_up_table, 0))
        # index of R starts from 1, and point cant be greater than the number of samples
        xth_point_of_look_up_table = max(0, min(xth_point, samples_in_look_up_table - 1))

        xth_value = look_up_table.iloc[xth_point_of_look_up_table].item()

        return xth_value

    def upscale_dataframe(self, hypercube_dataframe):
        up_scaled = deepcopy(hypercube_dataframe)
        for key in hypercube_dataframe.columns:
            for row in range(hypercube_dataframe.shape[0]):
                up_scaled[key].iloc[row] = self.function_look_up_table(
                    key, hypercube_dataframe[key].iloc[row])

        return up_scaled

    def function_downscale_value(self,
                                 key,
                                 up_scaled_value,
                                 index_search_function=None,
                                 estimate_function=None):
        if index_search_function is None:
            index_search_function = self.log_search
        if estimate_function is None:
            estimate_function = self.down_scale_linearfit

        look_up_table = self.look_up_tables[key]

        lower_ind, upper_ind = index_search_function(look_up_table, up_scaled_value)

        hyper_cube_value = estimate_function(look_up_table, lower_ind, upper_ind, up_scaled_value)

        return hyper_cube_value

    def lin_search(self, look_up_table, up_scaled_value):

        samples_in_look_up_table = look_up_table.shape[0]
        last_index = samples_in_look_up_table - 1

        try:
            upper_ind = next(idx for idx, value in enumerate(
                look_up_table.values) if value > up_scaled_value)
        except StopIteration:
            upper_ind = last_index

        if upper_ind == last_index:
            lower_ind = last_index
        else:
            lower_ind = max(upper_ind - 1, 0)

        return lower_ind, upper_ind

    def log_search(self, look_up_table, up_scaled_value):
        upper_ind = bisect_right(look_up_table.values, up_scaled_value)
        samples_in_look_up_table = look_up_table.shape[0]
        last_index = samples_in_look_up_table - 1

        upper_ind = min(upper_ind, last_index)

        lower_ind = max(upper_ind - 1, 0)

        return lower_ind, upper_ind

    def down_scale_mean(self, look_up_table, lower_ind, upper_ind, up_scaled_value):

        samples_in_look_up_table = look_up_table.shape[0]
        hyper_cube_value = ((lower_ind + upper_ind) / 2) / samples_in_look_up_table

        return hyper_cube_value

    def down_scale_linearfit(self, look_up_table, lower_ind, upper_ind, up_scaled_value):
        samples_in_look_up_table = look_up_table.shape[0]
        upper_value = look_up_table.iloc[upper_ind]
        lower_value = look_up_table.iloc[lower_ind]

        x = numpy.array([lower_value, upper_value]).reshape(-1, 1)
        y = numpy.array([lower_ind, upper_ind])
        reg = LinearRegression().fit(x, y)

        lin_fit_ind = reg.predict(numpy.array([up_scaled_value]).reshape(-1, 1)).item()

        hyper_cube_value = lin_fit_ind / samples_in_look_up_table

        return hyper_cube_value

    def downscale_dataframe(self,
                            up_scaled,
                            index_search_function=None,
                            estimate_function=None):

        if index_search_function is None:
            index_search_function = self.log_search
        if estimate_function is None:
            estimate_function = self.down_scale_mean

        if "pblh" in up_scaled.columns:
            up_scaled["pbl"] = up_scaled["pblh"]
            up_scaled.drop(columns="pblh", inplace=True)

        hypercube_dataframe = deepcopy(up_scaled)

        for key in up_scaled.columns:
            for row in range(up_scaled.shape[0]):
                hypercube_dataframe[key].iloc[row] = self.function_downscale_value(
                    key, up_scaled[key].iloc[row], index_search_function, estimate_function)

        return hypercube_dataframe

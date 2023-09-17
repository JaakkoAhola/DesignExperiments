#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
import os
import pathlib
import pandas
import numpy
from copy import deepcopy
from bisect import bisect_right
from itertools import repeat
from sklearn.linear_model import LinearRegression

# package imports
from library import Data

from dotenv import load_dotenv
load_dotenv()


class LookUpTable:

    def __init__(self, variable=None, debug=False):

        valid_variables = ["q_inv", "tpot_inv", "lwp", "tpot_pbl",
                           "pbl", "cdnc", "ks", "as", "cs", "rdry_AS_eff", "cos_mu"]

        if variable is None:

            self.selected_variables = valid_variables

        else:
            for var in variable:
                assert var in valid_variables

            self.selected_variables = variable

        self.mainfolder = pathlib.Path(os.environ["REPO"]) / "data/01_source"
        if debug:
            self.collection_filename = self.mainfolder / "sample20000.csv"
        else:
            self.collection_filename = self.mainfolder / "eclair_dataset_2001_designvariables.csv"

        self.collection_dataframe = None

        self.look_up_tables = dict(zip(self.selected_variables, repeat(None)))

    def __init__wrapper(self):
        self.create_look_up_tables()
        self.load_look_up_tables()

    def load_collection(self):
        self.collection_dataframe = pandas.read_csv(self.collection_filename, index_col=0)

        return self.collection_dataframe

    def get_collection_dataframe(self):
        return self.collection_dataframe

    def add_suffix_to_duplicates(self, series):
        name = series.name
        values = series.values
        unique_values, indices, counts = numpy.unique(values, return_counts=True, return_index=True)
        is_duplicate = counts > 1

        ordinal_numbers = numpy.zeros(len(series), dtype=int)
        for value, count in zip(unique_values[is_duplicate], counts[is_duplicate]):
            duplicate_indices = numpy.where(values == value)[0]
            ordinal_numbers[duplicate_indices] = numpy.arange(1, count + 1)

        mask = is_duplicate[indices.searchsorted(numpy.arange(len(series)), side='right') - 1]

        result_series = [
            f"{value}_1{ordinal}" if is_dup else str(value)
            for value, is_dup, ordinal in zip(values, mask, ordinal_numbers)
        ]

        return pandas.Series(result_series, name=name)

    def create_look_up_tables(self):
        for key in self.selected_variables:
            print()
            print(f"Creating lookup table for variable {key}")
            file = self.mainfolder / (self.collection_filename.stem +
                                      "_look_up_table_" + key + ".csv")
            if file.is_file():
                print(f"Lookup table for variable {key} already exists")
                next
            else:
                if self.collection_dataframe is None:
                    print("Let us read the source")
                    self.load_collection()

                if (key in ["cos_mu", "rdry_AS_eff"]):
                    print(f"For variable {key} let us filter out values smaller than epsilon.")
                    filtered_data = deepcopy(
                        self.collection_dataframe[self.collection_dataframe[key] > Data.getEpsilon()])

                else:
                    filtered_data = deepcopy(self.collection_dataframe)

                print(f"Let us sort the values for variable {key}")
                sorted_dataframe = filtered_data.sort_values(key)
                print(f"Values sorted for {key}")
                sorted_series = sorted_dataframe[key]
                sorted_series = sorted_series.reset_index(drop=True)

                sorted_non_duplicate = self.add_suffix_to_duplicates(sorted_series)

                print(f"Save lookup table for variable {key}")
                sorted_non_duplicate.to_csv(file, index=False)
                print(f"Lookuptable creation finished for variable {key}.")

    def load_look_up_tables(self):
        for key in self.selected_variables:
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

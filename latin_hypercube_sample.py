#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 18:42:33 2021

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
import time
from scipy.stats import qmc
import sys
import os
import pandas
import pathlib
sys.path.append(os.environ["LESMAINSCRIPTS"])
from Colorful import Colorful
from Data import Data
from Figure import Figure
from PlotTweak import PlotTweak


class latin_hypercube_sample():

    def __init__(self,
                 files={"big": "/home/aholaj/Data/ECLAIR/eclair_dataset_2001_designvariables.csv",
                          "sample": "/home/aholaj/Data/ECLAIR/sample.csv"
                              , }
                 ):
        self.files = {}
        for key in files.keys():
            self.files[key] = pathlib.Path(files[key])
        self.dataframes = {}

    def read_big(self):
        self.dataframes["big"] = pandas.read_csv(self.files["big"],
                                                 index_col=0)

    def read_sample(self):
        self.dataframes["sample"] = pandas.read_csv(self.files["sample"],
                                                    index_col=0)

    def create_sample(self, sample_n=1000):
        assert("big" in self.dataframes)
        self.dataframes["sample"] = self.dataframes["big"].sample(n=sample_n,
                                                                  random_state=0)

    def write_sample(self):
        assert("sample" in self.dataframes)
        self.dataframes["sample"].to_csv(self.files["sample"])

    def get_lhs_sample(self, samples=10, dimensions=2):

        sampler = qmc.LatinHypercube(d=dimensions)

        self.lhs_sample = sampler.random(n=samples)

    def get_lhs_sample_as_dataframe(self, columns=["x", "y"]):
        assert(len(columns) == self.lhs_sample.shape[1])

        self.lhs_sample_dataframe = pandas.DataFrame(
            data=self.lhs_sample,
            columns=columns)

    def lhs_figure(self):
        fig = Figure(".", "lhs")

        ax = fig.getAxes()

        self.lhs_sample.plot.scatter(x="x", y="y", ax=ax)

        fig.save()









if __name__ == "__main__":
    start = time.time()
    latin = latin_hypercube_sample()
    end = time.time()
    print(f"\nScript completed in { end - start : .1f} seconds")
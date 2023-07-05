#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
import os
import sys
import pandas
import time
from datetime import datetime
from scipy.stats import qmc
sys.path.append(os.environ["LESMAINSCRIPTS"])
from Figure import Figure


def figure_lhs(self):
    assert hasattr(self, "lhs_sample_dataframe")

    lhs_figure_name = "lhs"

    self.figures[lhs_figure_name] = Figure(self.figure_folder,
                                           lhs_figure_name)

    fig = self.figures[lhs_figure_name]

    ax = fig.getAxes()

    self.lhs_sample_dataframe.plot.scatter(x="x", y="y", ax=ax)


def get_lhs_sample(self, samples=10, dimensions=2):

    sampler = qmc.LatinHypercube(d=dimensions)

    self.lhs_sample = sampler.random(n=samples)

    return self.lhs_sample


def get_lhs_sample_as_dataframe(self, columns=["x", "y"]):
    assert len(columns) == self.lhs_sample.shape[1]

    self.lhs_sample_dataframe = pandas.DataFrame(
        data=self.lhs_sample,
        columns=columns)


def main():
    pass


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {(end - start):.2f} seconds.")

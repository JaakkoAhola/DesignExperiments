#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 18:43:55 2021

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
import unittest
import time
import os
import pathlib
import pandas
import numpy
from algorithms import SourceVsSampleVsDesign


class test_SourceVsSampleVsDesign(unittest.TestCase):

    def test_init(self):
        test_latin = SourceVsSampleVsDesign()
        self.assertTrue(hasattr(test_latin, "files"))
        self.assertTrue(hasattr(test_latin, "dataframes"))
        self.assertTrue(hasattr(test_latin, "figure_folder"))
        self.assertTrue(hasattr(test_latin, "figures"))

    @unittest.skip("a bit too time consuming")
    def test_read_big(self):
        test_latin = SourceVsSampleVsDesign()
        test_latin.read_big()
        self.assertTrue("big" in test_latin.dataframes)

    def test_read_sample(self):
        test_latin = SourceVsSampleVsDesign()
        test_latin.read_sample()
        self.assertTrue("sample" in test_latin.dataframes)

    @unittest.skip("a bit too time consuming")
    def test_create_sample(self):
        test_latin = SourceVsSampleVsDesign()
        samples = 1000
        test_latin.read_big()
        test_latin.create_sample(samples)

        self.assertTrue(isinstance(test_latin.dataframes["sample"],
                                   pandas.core.frame.DataFrame))
        self.assertEqual(samples, len(test_latin.dataframes["sample"]))

    def test_create_sample_uninitialised_big(self):
        with self.assertRaises(AssertionError):
            test_latin = SourceVsSampleVsDesign()
            test_latin.create_sample()

    @unittest.skip("a bit too time consuming")
    def test_write_sample(self):
        test_sample = "/tmp/test.csv"
        test_latin = SourceVsSampleVsDesign(files={"big": pathlib.Path(os.environ["REPO"]) /
                                                   "data/01_source/eclair_dataset_2001_designvariables.csv",
                                                   "sample": test_sample})
        test_latin.read_big()
        test_latin.create_sample(1)
        test_latin.write_sample()
        test_latin.files["sample"].is_file()
        os.remove(test_sample)

    def test_write_sample_uninitialised_sample(self):
        with self.assertRaises(AssertionError):
            test_latin = SourceVsSampleVsDesign()
            test_latin.write_sample()

    def test_get_lhs_sample(self):
        test_latin = SourceVsSampleVsDesign()
        test_latin.get_lhs_sample(1, 1)

        self.assertTrue(isinstance(test_latin.lhs_sample, numpy.ndarray))

        self.assertEqual(test_latin.lhs_sample.shape,
                         numpy.zeros([1, 1]).shape)

    def test_get_lhs_sample_as_dataframe(self):
        test_latin = SourceVsSampleVsDesign()
        self.assertTrue(callable(test_latin.get_lhs_sample_as_dataframe))

        test_latin.get_lhs_sample(1, 2)
        test_latin.get_lhs_sample_as_dataframe()
        self.assertTrue(hasattr(test_latin, "lhs_sample_dataframe"))
        self.assertTrue((test_latin.lhs_sample_dataframe, pandas.core.frame.DataFrame))

        with self.assertRaises(AssertionError):
            test_latin.get_lhs_sample(1, 1)
            test_latin.get_lhs_sample_as_dataframe()

    def test_finalise_figures(self):
        test_latin = SourceVsSampleVsDesign()
        self.assertTrue(callable(test_latin.finalise_figures))

    def test_figure_lhs(self):
        test_latin = SourceVsSampleVsDesign(figure_folder="/tmp/figures")

        self.assertTrue(callable(test_latin.figure_lhs))

        test_latin.get_lhs_sample()
        test_latin.get_lhs_sample_as_dataframe()
        test_latin.figure_lhs()
        self.assertTrue("lhs" in test_latin.figures)

        with self.assertRaises(AssertionError):
            test_latin2 = SourceVsSampleVsDesign()
            test_latin2.figure_lhs()

    # def test_lhs


if __name__ == "__main__":
    start = time.time()
    unittest.main()
    end = time.time()
    print(f"\nScript completed in { end - start : .1f} seconds")

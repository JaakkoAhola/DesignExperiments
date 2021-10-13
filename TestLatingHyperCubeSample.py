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
import pandas
import numpy
from latin_hypercube_sample import latin_hypercube_sample


class test_latin_hypercube_sample(unittest.TestCase):

    def test_init(self):
        test_latin = latin_hypercube_sample()
        self.assertTrue(hasattr(test_latin, "files"))
        self.assertTrue(hasattr(test_latin, "dataframes"))

    @unittest.skip("a bit too time consuming")
    def test_read_big(self):
        test_latin = latin_hypercube_sample()
        test_latin.read_big()
        self.assertTrue("big" in test_latin.dataframes)

    def test_read_sample(self):
        test_latin = latin_hypercube_sample()
        test_latin.read_sample()
        self.assertTrue("sample" in test_latin.dataframes)

    @unittest.skip("a bit too time consuming")
    def test_create_sample(self):
        test_latin = latin_hypercube_sample()
        samples = 1000
        test_latin.read_big()
        test_latin.create_sample(samples)

        self.assertTrue(isinstance(test_latin.dataframes["sample"],
                                   pandas.core.frame.DataFrame))
        self.assertEqual(samples, len(test_latin.dataframes["sample"]))

    def test_create_sample_uninitialised_big(self):
        with self.assertRaises(AssertionError):
            test_latin = latin_hypercube_sample()
            test_latin.create_sample()

    @unittest.skip("a bit too time consuming")
    def test_write_sample(self):
        test_sample = "/tmp/test.csv"
        test_latin = latin_hypercube_sample(files={"big": "/home/aholaj/Data/ECLAIR/eclair_dataset_2001_designvariables.csv",
                                                   "sample": test_sample})
        test_latin.read_big()
        test_latin.create_sample(1)
        test_latin.write_sample()
        test_latin.files["sample"].is_file()
        os.remove(test_sample)

    def test_write_sample_uninitialised_sample(self):
        with self.assertRaises(AssertionError):
            test_latin = latin_hypercube_sample()
            test_latin.write_sample()

    def test_get_lhs_sample(self):
        test_latin = latin_hypercube_sample()
        test_latin.get_lhs_sample(1, 1)

        self.assertTrue(isinstance(test_latin.lhs_sample, numpy.ndarray))

        self.assertEqual(test_latin.lhs_sample.shape,
                         numpy.zeros([1, 1]).shape)

    def test_get_lhs_sample_as_dataframe(self):
        test_latin = latin_hypercube_sample()
        self.assertTrue(callable(test_latin.get_lhs_sample_as_dataframe))

        test_latin.get_lhs_sample(1, 2)
        test_latin.get_lhs_sample_as_dataframe()
        self.assertTrue(hasattr(test_latin, "lhs_sample_dataframe"))
        self.assertTrue((test_latin.lhs_sample_dataframe, pandas.core.frame.DataFrame))

        with self.assertRaises(AssertionError):
            test_latin.get_lhs_sample(1, 1)
            test_latin.get_lhs_sample_as_dataframe()







if __name__ == "__main__":
    start = time.time()
    unittest.main()
    end = time.time()
    print(f"\nScript completed in { end - start : .1f} seconds")
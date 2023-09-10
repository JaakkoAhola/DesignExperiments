#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@affiliation:  University of Turku
@date: 4.7.2023
@licence: MIT licence Copyright
"""
import os
import unittest


class ImportTest(unittest.TestCase):
    def test_imports(self):
        # List all Python files in the current directory
        python_files = [file for file in os.listdir('.') if file.endswith('.py')]
        print(python_files)
        # Iterate over the Python files and test imports
        for file in python_files:
            filename = os.path.splitext(file)[0]
            try:
                exec(f'import {filename}')
                self.assertTrue(True, f"Import test passed for {file}")
            except ImportError:
                self.fail(f"Import test failed for {file}")

            try:
                exec(f'from {filename} import *')
                self.assertTrue(True, f"From import test passed for {file}")
            except ImportError:
                self.fail(f"From import test failed for {file}")

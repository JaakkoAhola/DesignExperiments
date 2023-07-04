#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 20 19:13:17 2021

@author: Jaakko Ahola, Finnish Meteorological Institute
@licence: MIT licence Copyright
"""
from copy import deepcopy
import sys
import pandas
import os

from scipy.stats import qmc
from sklearn.preprocessing import StandardScaler

sys.path.append(os.environ["CODEX"] +
                "/LES-superfolder/LES-emulator-02postpros")
from SourceVsSampleVsDesign import SourceVsSampleVsDesign
import LES2emu


class LatinHyperCubeSampleDesign:

    def __init__(self):

        latin = SourceVsSampleVsDesign()

        self.sb_night_variables = [
            'q_inv', 'tpot_inv', 'lwp', 'tpot_pbl', 'pbl', 'cdnc']
        self.sb_night_sample = deepcopy(
            latin.get_sample()[self.sb_night_variables])

        self.scaler_dict = {}
        self.lhs_sample_normalized = None
        self.lhs_as_transformed = None
        self.scaled_names = []
        self.lower_bounds = []
        self.upper_bounds = []
        self.design_latin_plain = None

    def get_full_design_lhs(self):
        self.init_normalised_latin()
        self.get_scaled_features()
        self.get_transformed_latin()
        data_frame = self.get_design_latin_plain()

        return data_frame

    def init_normalised_latin(self):

        sampler = qmc.LatinHypercube(d=6)
        self.lhs_sample_normalized = sampler.random(n=500)
        print(qmc.discrepancy(self.lhs_sample_normalized))

        return self.lhs_sample_normalized

    def get_scaled_features(self):

        for key in self.sb_night_sample.keys():
            print(key)
            param_values = self.sb_night_sample[key].values.reshape(-1, 1)
            scaler = StandardScaler().fit(param_values)
            transformed = scaler.transform(param_values)
            self.sb_night_sample[key + "_scaled"] = transformed.reshape(-1,)
            self.scaler_dict[key] = scaler

        return self.scaler_dict

    def get_transformed_latin(self):

        for key in self.sb_night_sample:
            if "_scaled" in key:
                self.scaled_names.append(key)
                self.lower_bounds.append(self.sb_night_sample[key].min())
                self.upper_bounds.append(self.sb_night_sample[key].max())

        self.lhs_as_transformed = qmc.scale(self.lhs_sample_normalized,
                                            self.lower_bounds,
                                            self.upper_bounds)

        return self.lhs_as_transformed

    def get_design_latin_plain(self):
        lhs_plain = {}
        for ind, key in enumerate(self.sb_night_variables):
            lhs_plain[key] = self.scaler_dict[key].inverse_transform(
                self.lhs_as_transformed[:, ind].reshape(-1, 1)).reshape(-1, )

        self.design_latin_plain = pandas.DataFrame.from_dict(lhs_plain)

        return self.design_latin_plain

    def get_humidity_jump(self):

        self.design_latin_plain["aux_q_pbl_kg_kg"] = self.design_latin_plain.apply(lambda row:
                                                                                   LES2emu.solve_rw_lwp(101780,
                                                                                                        row["tpot_pbl"],
                                                                                                        row["lwp"]
                                                                                                        * 1e-3,
                                                                                                        row["pbl"] * 100.),
                                                                                   axis=1)

    def get_pblh_in_meters(self):
        self.design_latin_plain["aux_pblh_m"] = self.design_latin_plain.apply(lambda row:
                                                                              LES2emu.calc_lwp(101780,
                                                                                               row["tpot_pbl"],
                                                                                               row["pbl"]
                                                                                               * 100.,
                                                                                               row["aux_q_pbl_kg_kg"])[2], axis=1)

    def get_humidity_jump_in_grams(self):

        self.design_latin_plain["aux_q_pbl_g_kg"] = self.design_latin_plain["aux_q_pbl_kg_kg"] * 1e3

    def check_humidity_constraint(self):
        self.design_latin_plain["q_constraint"] = self.design_latin_plain.apply(lambda row:
                                                                                row["q_inv"] < row["aux_q_pbl_g_kg"],
                                                                                axis=1)

    def write_design_latin(self):
        self.design_latin_plain.to_csv(
            os.environ["DESIGNRESULTS"] + "/design_lhs_sb_night_500_c.csv")

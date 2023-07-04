#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
University of Turku
@date: 4.7.2023
"""

import numpy
from scipy.spatial import distance


def generalised_distance(x_array, y_array, s=2):
    p = x_array.shape[0]

    dist = numpy.power(numpy.sum(numpy.power(
        numpy.abs(x_array - y_array), s)) / p, 1 / s)

    return dist


def logarithmic_euclidian_distance(x, y):
    x_log = numpy.log(x)
    y_log = numpy.log(y)

    return distance.euclidean(x_log, y_log)


def matrix_minimum_distance(mm, dist_func=distance.euclidean):
    minimum = numpy.nan

    for row in range(mm.shape[0]):
        for otherRow in range(row, mm.shape[0]):
            if row != otherRow:
                dd = dist_func(mm[row, ], mm[otherRow, ])
                minimum = numpy.nanmin([dd, minimum])
    return minimum


def max_pro_measure(mm):
    distance_prod = numpy.zeros(mm.shape[0])
    for row in range(mm.shape[0]):
        for otherRow in range(row, mm.shape[0]):
            if row != otherRow:
                distance_prod[row] = numpy.power(numpy.prod(
                    numpy.power(mm[row, ] - mm[otherRow, ], 2)), -1)

    maxpro = numpy.power(numpy.mean(distance_prod), 1. / mm.shape[1])

    return maxpro

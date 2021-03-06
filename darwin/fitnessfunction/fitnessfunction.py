#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import abstractmethod, ABCMeta


class FitnessFunction(object):
    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        self.results_file = None

    @abstractmethod
    def fitness(self, model):
        pass

    def log_results(self, filename):
        self.results_file = filename

    def darwin_init_actions(self):
        pass


class Fitness(object):
    def __init__(self, value, data):
        self.value = value
        self.data = data

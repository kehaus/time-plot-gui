#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 16:01:02 2020
​
@author: kh
"""

import os
from os import path
import json
import numpy as np

# ===========================================================================
# helper class to save&store JSON files
# ===========================================================================
class JSONFileHandler():

    def load(self, fn, mode='r'):
        with open(fn, mode=mode) as json_file:
            data = json.load(json_file)
        return data

    def save(self, fn, dct, mode='a', sort_keys=True, indent=4):
        with open(fn, mode=mode) as outfile:
            json.dump(dct, outfile, sort_keys=sort_keys, indent=indent)
        return

# ===========================================================================
#
# ===========================================================================


class PlotItemSettings(JSONFileHandler):
    """ """

    SETTINGS_FILENAME = "custom_settings.json"
    DEFAULT_SETTINGS = {
        'autoPan':          False,
        'xscalelog':        False,
        'yscalelog':        False,
        'xlim':             [0, 1],
        'ylim':             [-1,1],
        'xautorange':       True,
        'yautorange':       True,
        'xgridlines':       False,
        'ygridlines':       False,
        'gridopacity':      3,
        'line_settings':    {},
        'plotalpha':        [1, False],
        # mouseMode 1 means rectangle zooming and 3 means pan zooming
        'mouseMode':        1,
        'x_zoom':           True,
        'y_zoom':           True,
        'auto_clear_data':  True
        # in plotalpha, the first item is the alpha and the second is whether the value is autodetermined
        # maybe more settings here
        }

    def __init__(self, number_of_lines = 1):
        self.settings_filename = PlotItemSettings.SETTINGS_FILENAME
        settings = self._checks_for_settings_file()
        self.number_of_lines = number_of_lines
        if settings != {}:
            self.settings = settings
        else:
            self.settings = PlotItemSettings.DEFAULT_SETTINGS
        self.set_line_settings(self.number_of_lines)

    # =====
    # define function which automatically checks for settings file
    # =====

    def _checks_for_settings_file(self):
        """checks if settings file in workdir and imports it.

        If no settings file is present in the working directory, returns an
        empty dictionary

        """
        # implement function wich checks if settings file present.
        #   return {} if not the case
        if path.exists(self.settings_filename):
            custom_settings = self.load(self.settings_filename)
            return custom_settings
        return {}

    def set_line_settings(self, number_of_lines):
        keys = range(number_of_lines)
        default_line_settings = {'line_alpha': 1}
        line_settings = {key: default_line_settings for key in keys}
        self.settings.update(line_settings = line_settings)

    # ====
    # define functions which load and save settings files/ dictionaries
    # ====

    def update(self, **kwargs):
        self.settings.update(**kwargs)

    def save_settings(self, **kwargs):
        self.update(**kwargs)
        if path.exists(self.settings_filename):
            os.remove(self.settings_filename)
        self.save(self.settings_filename, self.settings)
        return

    # ===
    # define setter and getter for all settings
    # ===

    def __getattr__(self, name):
        """returns self.settings[name] if name is key in settings dictionary
        """
        if 'settings' in self.__dict__:
            keys = self.settings.keys()
        else:
            keys = []

        if name in keys:
            return self.settings[name]
        else:
            return super(PlotItemSettings, self).__getattribute__(name)

    def __setattr__(self, name, value):
        """sets self.settings[name]=value if name is key in settings dictionary
        """
        if 'settings' in self.__dict__:
            keys = self.settings.keys()
        else:
            keys = []

        if name in keys:
            self.settings[name] = value
        else:
            super(PlotItemSettings, self).__setattr__(name, value)

class DataRecall(object):
    """ """
    STORED_DATA_FILENAME = "stored_data.json"

    def __init__(self):
        self.stored_data_filename = DataRecall.STORED_DATA_FILENAME

    def store(self, time, absolute_time, y):
        """store collected data to json file """

        if path.exists(self.stored_data_filename):
            os.remove(self.stored_data_filename)

        with open(self.stored_data_filename, 'w') as outfile:
            json.dump({'time': time, 'absolute_time': absolute_time, 'y': y}, outfile)

        return

    def load_data(self, file = None):
        """load stored data from json file"""
        # code to load settgins from file here
        if file is None:
            file = self.stored_data_filename
        if path.exists(file):
            with open(file) as json_file:
                data = json.load(json_file)
            return np.array(data['time']), np.array(data['absolute_time']), np.array(data['y'])
        return np.array([]), np.array([]), np.array([])

    def clear_data(self):
        if path.exists(self.stored_data_filename):
            os.remove(self.stored_data_filename)


if __name__ == "__main__":
    ps = PlotItemSettings()


    # ============================
    # Example how to change settings values
    # ============================
    ps.xlim             # get values back
    ps.xlim = [0,2]     # set values

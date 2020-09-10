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
    FOLDER_FILENAME = "saved_info"
    SETTINGS_FILENAME = "custom_settings.json"

    DEFAULT_SETTINGS = {
        'autoPan':              False,
        'xscalelog':            False,
        'yscalelog':            False,
        'xlim':                 [0, 1],
        'ylim':                 [-1,1],
        'xautorange':           True,
        'yautorange':           True,
        'xgridlines':           True,
        'ygridlines':           True,
        'gridopacity':          3,
        'line_settings':        {},
        'plotalpha':            [1, False],
        # mouseMode 1 means rectangle zooming and 3 means pan zooming
        'mouseMode':            1,
        'x_zoom':               True,
        'y_zoom':               True,
        'auto_clear_data':      True,
        'zoom_lines':           [0, 1, -1, 1],
        'frequency_state':      False,
        'labels':               {'title_text':          'TimePlotGui',
                                'title_font_size':      20,
                                'title_font_color':     '#FFF',
                                'x_axis_data_type':     "Time",
                                'x_axis_unit':          "s",
                                'x_axis_font_size':     15,
                                'x_axis_font_color':    '#FFF',
                                'y_axis_data_type':     "Signal",
                                'y_axis_unit':          "a.u.",
                                'y_axis_font_size':     15,
                                'y_axis_font_color':    '#FFF'
                                },
        'relative_timestamp':   True,
        'do_autosave':          True,
        'autosave_nr':          30,
        'autoVisibleOnly_x':    False,
        'autoVisibleOnly_y':    False
        # in plotalpha, the first item is the alpha and the second is whether the value is autodetermined
        # maybe more settings here
        }

    def __init__(self, number_of_lines = 1, folder_filename = None, unusal_settings_file = None):
        if folder_filename is not None:
            self.folder_filename = folder_filename
        else:
            self.folder_filename = self.FOLDER_FILENAME
        if unusal_settings_file is None:
            self.settings_filename = os.path.join(self.folder_filename, PlotItemSettings.SETTINGS_FILENAME)
        else:
            self.settings_filename = unusal_settings_file
        #self.settings_filename = PlotItemSettings.SETTINGS_FILENAME
        if not os.path.exists(self.folder_filename):
            os.makedirs(self.folder_filename)
        settings = self._checks_for_settings_file()
        self.number_of_lines = number_of_lines
        self.set_line_settings(self.number_of_lines)
        if settings != {}:
            self.settings = settings
        else:
            self.settings = PlotItemSettings.DEFAULT_SETTINGS

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
        self.default_line_settings = {'line_alpha': 1, 'line_width': 1, 'line_color': (255, 255, 255, 255)}
        line_settings = {str(key): self.default_line_settings for key in keys}
        self.DEFAULT_SETTINGS.update(line_settings = line_settings)

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

if __name__ == "__main__":
    ps = PlotItemSettings()


    # ============================
    # Example how to change settings values
    # ============================
    ps.xlim             # get values back
    ps.xlim = [0,2]     # set values

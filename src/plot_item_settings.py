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

class PlotItemSettings(object):
    """ """

    settings_filename = "custom_settings.json"
    DEFAULT_SETTINGS = {    # i just used generic values inhere. change if necessary
        'autoPan':      True,
        'xscale':      'linear',
        'yscale':      'linear',
        'xlim':         [0,1],
        'ylim':         [0,1],
        # maybe more settings here
        }

    def __init__(self):
        #print(f"initializing settings")
        settings = self._checks_for_settings_file()
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
            custom_settings = self.load()
            return custom_settings
        return {}

    # ====
    # define functions which load and save settings files/ dictionaries
    # ====

    def load(self):
        """load settings from file"""
        # code to load settgins from file here
        with open(self.settings_filename) as json_file:
            data = json.load(json_file)
            custom_settings = data['custom_settings'][-1]
            # for p in data['custom_settings']:
            #         print(p['autoPan'])
            #custom_settings = data['custom_settings'][-1]
        return custom_settings

    def save(self):
        """save settings to file """
        # code to save settings to file here
        data = {}
        data['custom_settings'] = []
        # data['custom_settings'].append({
        #     'autoPan': 'True',
        #     'xscale': 'linear',
        #     'yscale': 'log',
        #     'xlim': '[-2,10]',
        #     'ylim': '[0,1]'
        # })
        for key in self.settings:
            print(f"{key}")
            print(f"{self.__getattr__(key)}")
            data['custom_settings'].append({
                key: self.__getattr__(key)
            })

        if path.exists(self.settings_filename):
            os.remove(self.settings_filename)

        with open(self.settings_filename, 'w') as outfile:
            json.dump(data, outfile)

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

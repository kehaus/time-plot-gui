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

    DEFAULT_SETTINGS = {    # i just used generic values inhere. change if necessary

        'autoPan':      True,
        'xscale':      'linear',
        'yscale':      'linear',
        'xlim':         [0,1],
        'ylim':         [0,1],
        # maybe more settings here
        }

    def __init__(self):
        print(f"initializing settings")
        settings = self._checks_for_settings_file()
        if settings != {}:
            print(f"setting customs")
            self.settings = settings
        else:
            print(f"setting defaults")
            self.settings = PlotItemSettings.DEFAULT_SETTINGS

    # =====
    # define function which automatically checks for settings file
    # =====

    def _checks_for_settings_file(self):
        """checks if settings file in workdir and imports it.

        If no settings file is present in the working directory, returns an
        empty dictionary

        """
        if path.exists("custom_settings.txt"):
            print(f"custom file exists")
            custom_settings = self.load()
            return custom_settings
        # implement function wich checks if settings file present.
        #   return {} if not the case
        print(f"custom file doesnt exist")
        return {}

    # ====
    # define functions which load and save settings files/ dictionaries
    # ====

    def load(self):
        """load settings from file"""
        # code to load settgins from file here
        with open('custom_settings.txt') as json_file:
            data = json.load(json_file)
            custom_settings = data['custom_settings'][-1]
            for p in data['custom_settings']:
                    print(p['autoPan'])
            #custom_settings = data['custom_settings'][-1]
        return custom_settings

    def save(self):
        """save settings to file """
        # code to save settings to file here
        data = {}
        data['custom_settings'] = []
        data['custom_settings'].append({
            'autoPan': 'True',
            'xscale': 'linear',
            'yscale': 'log',
            'xlim': self.get_xlim(),
            'ylim': '[0,1]'
        })
        print(f"{data}")

        if path.exists("custom_settings.txt"):
            os.remove("custom_settings.txt")

        with open('custom_settings.txt', 'w') as outfile:
            json.dump(data, outfile)

        return

    # ===
    # define setter and getter for all settings
    # ===

    def get_xlim(self):
        #return self.settings['xlim']
        xlim = [1, 10]
        return xlim

    def set_xlim(self, xlim):
        self.settings['xlim'] = xlim

    #  ... the same for the others



if __name__ == "__main__":
    ps = PlotItemSettings()

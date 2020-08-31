#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PlotSettings item class allows to load, access and save plot settings.


Example
-------
    >>> ps = PlotItemSettings()
    >>> ps.xlim             # get values back
    >>> ps.xlim = [0,2]     # set values

"""

import os
from os import path
import json
import numpy as np

# ===========================================================================
# helper class to save&store JSON files
# ===========================================================================
class JSONFileHandler():
    """Base class to handle loading and saving from JSON files"""

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
    """
    Container to load, access, and save plot settings 
    
    Loads plot settings from json file or generate default settings if no valid
    path to a json file is provided on initialization.
    All keys in in the settings dictionary can also be accessed directly as 
    object attributes 

    
    Parameter
    ---------
    number_of_lines : int
        number of data lines present in plot
    folder_filename : str
        folder location where json settings file is located
    unusual_settings_file : str
        settings filename
        
    
    Attribute
    ---------
    folder_filename : str
        path to settings file
    settings_filename : str
        filename of the saved JSON file
    settings : dict
        contains all plot settings. 
    
    
    Settings description
    --------------------
    mouseMode : int
        1 means rectangle zooming and 3 means pan zooming
    plotalpha : lst
        first item is the alpha and the second is whether the value is 
        autodetermined
    
    
    Example
    -------
        >>> ps = PlotItemSettings()
        >>> ps.xlim             # get values back
        >>> ps.xlim = [0,2]     # set values

    
    """
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
        'mouseMode':            1,
        'x_zoom':               True,
        'y_zoom':               True,
        'auto_clear_data':      True,
        'zoom_lines':           [0, 1, -1, 1],
        'frequency_state':      False,
        'labels':               {'title_text':          'Test',
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
        }

    DEFAULT_LINE_SETTINGS = {
        'line_alpha': 1, 
        'line_width': 1, 
        'line_color': (255, 255, 255, 255),
    }
    
    MOUSEMODE = {
        1:  'rect',
        3:  'pan'
    }

    def __init__(self, number_of_lines = 1, folder_filename = None, 
                 unusal_settings_file = None):
        self.n_lines = number_of_lines
    
        if folder_filename is None:
            self.folder_filename = self.FOLDER_FILENAME
        else: 
            self.folder_filename = folder_filename
    
        if unusal_settings_file is None:
            self.settings_filename = os.path.join(
                self.folder_filename, 
                PlotItemSettings.SETTINGS_FILENAME
            )
        else:
            self.settings_filename = unusal_settings_file
        
        if not os.path.exists(self.folder_filename):
            os.makedirs(self.folder_filename)
        
        settings = self._load_settings_file()
        if settings != {}:
            self.settings = settings
        else:
            self.settings = self.get_default_settings(self.n_lines)

    def _load_settings_file(self):
        """checks if settings file in workdir and imports it.

        If no settings file is present in the working directory, returns an
        empty dictionary

        Return
        ------
        dct
            contains loaded settings. Empty if no settings file is found

        """
        if path.exists(self.settings_filename):
            custom_settings = self.load(self.settings_filename)
            return custom_settings
        return {}

        
    def get_default_settings(self, n_lines=None):
        """returns default settings dictionary
        
        Since number of lines is not know before initialization the complete
        default settings dictionary can only be constructed at initialization.
        This function updates the line settings item in the plot settings 
        dictionary with the correct number of lines and returns it
        
        Parameter
        ---------
        n_lines : int
            number of plotlines present in the plot
            
        Return
        ------
        dct
            settings dictionary; contains plot and line settings
            
        
        """
        if n_lines is None:
            n_lines = self.n_lines
        
        settings = PlotItemSettings.DEFAULT_SETTINGS.copy()
        line_setting = self.get_default_line_settings()
        all_line_settings = {
            str(key): line_setting.copy() for key in range(n_lines)
        }
        settings.update(
            line_settings = all_line_settings
        )
        return settings
    
    def restore_default_settings(self, keep_line_settings=False):
        """restores default settings from DEFAULT_SETTINGS dictionary
        
        Parameter
        ---------
        keep_line_settings : bool
            flag indicates if default line_settings should be restored as well
            
        """
        
        if keep_line_settings:
            tmp_line_settings = self.line_settings.copy()
        self.settings = self.get_default_settings()

        if keep_line_settings:
            self.line_settings.update(tmp_line_settings)
    
    def get_default_line_settings(self):
        """returns default line settings dictionary
        
        Return
        ------
        dct
            default settings for line element in plot item
            
        """
        return PlotItemSettings.DEFAULT_LINE_SETTINGS.copy()
    
    def clear_all_line_settings(self):
        """restores default line settings for all line setting entries"""
        for key in self.line_settings.keys():
            self.line_settings[key] = self.get_default_line_settings()

    def add_line(self):
        """add line to line_settings dictionary"""
        nr = len(self.line_settings)
        self.line_settings.update(
            {str(nr): self.get_default_line_settings()}
        )
        self._update_n_lines()
    
    def remove_line(self):
        """remove line from line settings dictionary"""
        self.line_settings.popitem()
        self._update_n_lines()
        
    def _update_n_lines(self):
        self.n_lines = len(self.settings['line_settings'])
        
    def get_nr_lines(self):
        """ returns number of lines"""
        return self.n_lines

    # ====
    # update, load, and save settings from/ to JSON file
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
    #  setter and getter to access settings
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 14 19:02:29 2020

@author: kh
"""

import os 
import sys
import time

import numpy as np
from PyQt5.QtWidgets import QApplication

test_mode = True
if not test_mode:
    from TimePlotGui import TimePlotGui, TimePlotMainWindow, DeviceWrapper, DummyDevice, start_application
else:
    module_path = os.path.dirname(os.getcwd())
    if module_path not in sys.path:
        sys.path.append(module_path)
    from src import TimePlotGui, TimePlotMainWindow, DeviceWrapper, DummyDevice, start_application
    
    
    
    
# ===========================================================================
# 1. define an Python class handling the hardware communication
#       this class needs to have a get_value function which returns the 
#       numerical value that should be plotted. 
#
# ===========================================================================
class SomeHardwareWrapper():
    
    def get_value(self):
        return np.random.rand()


# ===========================================================================
# start_gui function
# ===========================================================================
# def start_application(devices, MainWindowClass=None, **kwargs):
#     """starts instants of given MainWindowClass as QApplication with devices 
#     connected to it.
    
#     This function handles the QApplication start up of the gui. This procedure
#     and event handling is indepentent of the given MainWindowClass. It can also 
#     be used for other MainWindowClasses than the TimePlotMainWindow
    
    
#     Parameter
#     ---------
#     devices : DeviceWrapper object, list
#         represents the hardware. 
#     MainWindowClass : QMainWindow object
#         From this class an instance is created to generate the main window. If
#         None is passed a TimePlotMainWindow object is generated.
#     kwargs 
#         kwargs are passed to in the initialization of the MainWindowClass 
#         object
    
#     Return
#     ------
#         returns the inistialized MainWindowClass object
    
    
#     """
#     if MainWindowClass is None:
#         MainWindowClass = TimePlotMainWindow
    
#     app = QApplication.instance()
#     if app is None:
#         app = QApplication(sys.argv)
#     else:
#         print('QApplication instance already exists {}'.format(str(app)))
#     window = MainWindowClass(
#         devices=devices, **kwargs
#     )
#     try:
#         window.show()
#         app.exec_()
#     except:
#         window.closeEvent()
#     return window


# ============================================================================
# 2. Initialized hardware object and start Qapplication
# ============================================================================

# initilaze hardware wrapper (mocked in this example)
test_object = SomeHardwareWrapper()
dw = DeviceWrapper(test_object)

# initialized UI
start_application([dw], sampling_latency=0.05)





























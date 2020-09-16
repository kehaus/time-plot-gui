#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  4 06:25:36 2020

@author: kh
"""
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication

test_mode = True
if not test_mode:
    from TimePlotGui import TimePlotGui, DeviceWrapper, DummyDevice
else:
    module_path = os.path.dirname(os.getcwd())
    if module_path not in sys.path:
        sys.path.append(module_path)
    from src import TimePlotMainWindow, DeviceWrapper, DummyDevice
    from src.plot_item_settings import PlotItemSettings, JSONFileHandler


# ===========================================================================
# Run Gui 
# ===========================================================================
dd1 = DummyDevice(
    signal_form='random', xmin=0, xmax=2,
    frequency=5
)
dw1 = DeviceWrapper(dd1)

dd2 = DummyDevice(
    frequency=0.6
)
dw2 = DeviceWrapper(dd2)

dd3 = DummyDevice(
    signal_form='sin',
    frequency=1.3
)
dw3 = DeviceWrapper(dd3)


# ============================================================================
# Start TimePlotGui application
# ============================================================================
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)
else:
    print('QApplication instance already exists {}'.format(str(app)))
window = TimePlotMainWindow(devices=[dw1, dw2], sampling_latency=0.5)
try:
    window.show()
    app.exec_()
except:
    window.closeEvent()


# ===========================================================================
# investigate data
# ===========================================================================



json_handler = JSONFileHandler()
data_dct = json_handler.load(window.time_plot_ui.data_fn)


d0_2 = data_dct['data_0']
d1_2 = data_dct['data_1']




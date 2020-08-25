#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal working example to run TimePlotGui widget as MainWindow application
conncted to a DummyDevice class. The DummyDevice class mocks the hardware.


"""

import sys
from PyQt5.QtWidgets import QApplication


try:
    from .time_plot_gui import TimePlotMainWindow
    from .util.devicewrapper import DeviceWrapper
    from .util.dummydevice import DummyDevice
except:
    from time_plot_gui import TimePlotMainWindow
    from util.devicewrapper import DeviceWrapper
    from util.dummydevice import DummyDevice


# ============================================================================
# Create DummyDevice to mock connected hardware
# ============================================================================
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
window = TimePlotMainWindow(devicewrapper_lst=[dw1, dw2])
try:
    window.show()
    app.exec_()
except:
    window.closeEvent()

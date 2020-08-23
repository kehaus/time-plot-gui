#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This example script shows a minimal example for creating a gui object with an
TimePlotGui QWidget item and a control panel which allows to control hardware 
settings


TODO:
    * included detaile description on how to design the HardwareController

"""
__version__ = "1.0.0"

import os
from os import path
import ctypes as ct
import numpy as np
import time
from unittest.mock import MagicMock


import sys
import weakref
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition, QSize, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QMainWindow, QHBoxLayout
from PyQt5.QtWidgets import qApp, QAction, QMenu, QGridLayout, QLabel, QLineEdit, QSizePolicy, QFileDialog
from PyQt5.QtWidgets import QInputDialog, QColorDialog
from PyQt5.QtGui import QIcon, QFont, QCursor, QRegion, QPolygon, QWindow
from PyQt5 import QtCore, Qt, QtGui
import pyqtgraph as pg

from time_plot_gui import TimePlotGui
from util.devicewrapper import DeviceWrapper
from util.dummydevice import DummyDevice


class HardwareController(QMainWindow):
    """ """
    DEFAULT_GEOMETRY = [400, 200, 1000, 500]

    def __init__(self, devicewrapper_lst):
        super(HardwareController, self).__init__()
        self._init_ui(devicewrapper_lst = devicewrapper_lst)

    def _init_ui(self, devicewrapper_lst=None):
        self.setGeometry()
        self.setWindowTitle('time-plot')
        self.setStyleSheet("background-color: black;")
        
        # ===============================
        # Create TimePlotGui object
        # ===============================
        self.devicewrapper_lst = devicewrapper_lst
        self.time_plot_ui = TimePlotGui(
            parent=None,
            window=self,
            devicewrapper_lst=devicewrapper_lst,
            folder_filename = "gui",
            sampling_latency = .01
        )

        # ===============================
        # Customize UI
        #    This part sets up the control panel for communicating with the
        #    connected hardware
        # ===============================
        self.wdget = QWidget()
        self.layout = QGridLayout()
        self.setCentralWidget(self.wdget)

        self.layout.addWidget(self.time_plot_ui.central_wid, 0, 0, 6, 6)
        for idx, dw in enumerate(devicewrapper_lst):
            freq_inpt = QtGui.QInputDialog()
            freq_inpt.setStyleSheet("color: white")
            freq_inpt.setInputMode(0)
            freq_inpt.setLabelText("Frequency")
            freq_inpt.setOptions(freq_inpt.NoButtons)
            freq_inpt.setDoubleRange(1, 15)
            freq_inpt.setDoubleStep(.1)
            freq_inpt.setDoubleValue(2)
            freq_inpt.doubleValueChanged.connect(
                dw.set_frequency
            )
            self.layout.addWidget(freq_inpt, idx, 7, 1, 1)
        self.wdget.setLayout(self.layout)
    

    def setGeometry(self, *args, **kwargs):
        """ """
        if len(args) == 0 and len(kwargs) == 0:
            args = HardwareController.DEFAULT_GEOMETRY
        super(HardwareController, self).setGeometry(*args, **kwargs)

    def closeEvent(self, event):
        """ """
        # ===============================
        # close all the TimePlotGui objects. To avoid repeated popups, set 
        # auto_accept to True in all but one object (You can set all 
        # auto_accept arguments to True but it is not recommended so you dont 
        # close the gui accidentally)
        # ===============================
        self.time_plot_ui.closeEvent(event)


# ============================================================================
# main function
# ============================================================================
def main(devicewrapper_lst):
    """ """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print('QApplication instance already exists {}'.format(str(app)))
    window = HardwareController(
        devicewrapper_lst=devicewrapper_lst
    )
    try:
        window.show()
        app.exec_()
    except:
        window.closeEvent()


# ============================================================================
# main routine
# ============================================================================
if __name__ == "__main__":
    # ===============================
    # initilazed hardware wrapper (mocked)
    # ===============================
    dd1 = DummyDevice(
        signal_form='sin',
        frequency=1
    )
    dw1 = DeviceWrapper(dd1)

    dd2 = DummyDevice(
        frequency=0.6
    )
    dw2 = DeviceWrapper(dd2)

    # ===============================
    # initialized UI
    # ===============================
    main([dw1, dw2])

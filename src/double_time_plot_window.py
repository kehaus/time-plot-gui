"""
This example script shows a minimal example for creating a gui object 
containing two TimePlotGui objects.


TODO:
    * included detaile description on how to design the DoubleTimePlotWindow

"""
__version__ = "1.0.0"


import os
from os import path
import ctypes as ct
import numpy as np
import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition, QSize, QPoint
from unittest.mock import MagicMock


import sys
import weakref
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QMainWindow, QHBoxLayout
from PyQt5.QtWidgets import qApp, QAction, QMenu, QGridLayout, QLabel, QLineEdit, QSizePolicy, QFileDialog
from PyQt5.QtWidgets import QInputDialog, QColorDialog
from PyQt5.QtGui import QIcon, QFont, QCursor, QRegion, QPolygon, QWindow
from PyQt5 import QtCore, Qt, QtGui
import pyqtgraph as pg

from time_plot_gui import TimePlotGui
from util.devicewrapper import DeviceWrapper
from util.dummydevice import DummyDevice


class DoubleTimePlotWindow(QMainWindow):
    """ """
    
    DEFAULT_GEOMETRY = [400, 200, 1000, 500]

    def __init__(self, devicewrapper_lst1, devicewrapper_lst2):
        super(DoubleTimePlotWindow, self).__init__()
        self._init_ui(devicewrapper_lst1, devicewrapper_lst2)

    def _init_ui(self, devicewrapper_lst1, devicewrapper_lst2):
        self.setGeometry()
        self.setWindowTitle('time-plot')
        self.setStyleSheet("background-color: black;")
        
        # ===============================
        # Create TimePlotGui objects
        # ===============================
        self.time_plot_ui1 = TimePlotGui(
            parent=None,
            window=self,
            devicewrapper_lst=devicewrapper_lst1,
            folder_filename = "gui1"
        )
        self.time_plot_ui2 = TimePlotGui(
            parent=None,
            window=self,
            devicewrapper_lst=devicewrapper_lst2,
            folder_filename = "gui2"
        )

        # ===============================
        # Customize UI
        #    This part sets up the control panel with the two TimePlotGui QWidgets
        # ===============================
        self.wdget = QWidget()
        self.layout = QGridLayout()
        self.setCentralWidget(self.wdget)
        
        self.layout.addWidget(self.time_plot_ui1.central_wid, 0, 0, 1, 1)
        self.layout.addWidget(self.time_plot_ui2.central_wid, 0, 1, 1, 1)
        
        self.wdget.setLayout(self.layout)
    

    def setGeometry(self, *args, **kwargs):
        """ """
        if len(args) == 0 and len(kwargs) == 0:
            print('here')
            args = DoubleTimePlotWindow.DEFAULT_GEOMETRY
        super(DoubleTimePlotWindow, self).setGeometry(*args, **kwargs)


    def closeEvent(self, event):
        """ """
        # ===============================
        # close all the TimePlotGui objects. To avoid repeated popups, set 
        # auto_accept to True in all but one object (You can set all 
        # auto_accept arguments to True but it is not recommended so you dont 
        # close the gui accidentally)
        # ===============================
        close_accepted = self.time_plot_ui1.closeEvent(event)
        if close_accepted:
            self.time_plot_ui2.closeEvent(event, auto_accept = True)


# ============================================================================
# main function
# ============================================================================
def main(devicewrapper_lst1, devicewrapper_lst2):
    """ """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print('QApplication instance already exists {}'.format(str(app)))
    window = DoubleTimePlotWindow(
        devicewrapper_lst1=devicewrapper_lst1,
        devicewrapper_lst2=devicewrapper_lst2
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
    

    dd3 = DummyDevice(
        signal_form='sin',
        frequency=1.3
    )
    dw3 = DeviceWrapper(dd3)
    # ===============================
    # initialized UI
    # ===============================
    main([dw1], [dw2, dw3])


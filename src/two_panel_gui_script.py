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

from time_plot_gui import TimePlotGui, MainWindow
from util.devicewrapper import DeviceWrapper, DummyDevice


class PrimaryWindow(QMainWindow):
    """ """
    # xpos on screen, ypos on screen, width, height
    DEFAULT_GEOMETRY = [400, 200, 1000, 500]

    def __init__(self, devicewrapper_lst1 = None, devicewrapper_lst2 = None):
        super(PrimaryWindow, self).__init__()
        self._init_ui(devicewrapper_lst1 = devicewrapper_lst1, devicewrapper_lst2 = devicewrapper_lst2)

    def _init_ui(self, window_geometry=None, devicewrapper_lst1=None, devicewrapper_lst2 = None):
        self.setGeometry()
        self.setWindowTitle('time-plot')
        self.setStyleSheet("background-color: black;")
        self.time_plot_ui1 = TimePlotGui(
            parent=None,
            window=self,
            devicewrapper_lst=devicewrapper_lst1
        )
        self.time_plot_ui2 = TimePlotGui(
            parent=None,
            window=self,
            devicewrapper_lst=devicewrapper_lst2
        )
        self.button = QPushButton()
        self.button.setStyleSheet("background-color: rgb(120,120,120);")
        #self.time_plot_ui.setStyleSheet("background-color: rgb(120,120,120);")
        self.test_widget = QWidget()
        self.layout = QGridLayout()
        self.setCentralWidget(self.test_widget)
        self.layout.addWidget(self.time_plot_ui1.central_wid, 1, 1, 1, 1)
        self.layout.addWidget(self.time_plot_ui2.central_wid, 0, 0, 1, 1)
        self.layout.addWidget(self.button, 0, 1, 1, 1)
        self.test_widget.setLayout(self.layout)


    def setGeometry(self, *args, **kwargs):
        """ """
        if len(args) == 0 and len(kwargs) == 0:
            print('here')
            args = PrimaryWindow.DEFAULT_GEOMETRY
        super(PrimaryWindow, self).setGeometry(*args, **kwargs)

    def closeEvent(self, event):
        """ """
        print('event')
        self.time_plot_ui1.closeEvent(event)
#        event.accept

    def create_subwindow(self, width, height):
        self.subwindow = SubWindow()
        self.subwindow.create_window(width, height)
        self.subwindow.show()

def main(devicewrapper_lst1, devicewrapper_lst2):
    """ """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print('QApplication instance already exists {}'.format(str(app)))
    window = PrimaryWindow(
        devicewrapper_lst1=devicewrapper_lst1,
        devicewrapper_lst2=devicewrapper_lst2
    )
    try:
        window.show()
        app.exec_()
    except:
        window.closeEvent()

if __name__ == "__main__":
    dd1 = DummyDevice()
    dd1.frequency = 1
    dd1.signal_form = 'sin'
    dw1 = DeviceWrapper(dd1)

    dd2 = DummyDevice()
    dd2.frequency = 0.6
    dw2 = DeviceWrapper(dd2)

    dd3 = DummyDevice()
    dd3.frequency = 1.3
    dd3.signal_form = 'sin'
    dw3 = DeviceWrapper(dd3)

    main([dw1], [dw2])

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


class MultiPanelGui(QWidget):
    def __init__(self, parent=None, window=None, devicewrapper_lst1=None, devicewrapper_lst2 = None):
        """ """
        print(window)
        super(MultiPanelGui, self).__init__(parent=parent)
        self._init_ui(mainwindow = window, devicewrapper_lst1 = devicewrapper_lst1, devicewrapper_lst2 =devicewrapper_lst2)

    def _init_ui(self, mainwindow, devicewrapper_lst1, devicewrapper_lst2):
        """
        Creates and Loads the widgets in the GUI
        """
        # =====================================================================
        # Creates and configures central widget for window
        # =====================================================================
        print(mainwindow)
        self.central_wid = QWidget(mainwindow)
        self._set_central_wid_properties()
        self.mainwindow = mainwindow
        print(self.mainwindow)
        self.mainwindow.setCentralWidget(self.central_wid)
        # =====================================================================
        # control panel - initializes layout item to put widgets
        # =====================================================================
        self.graphics_layout = QGridLayout()

        self.mainwindow.create_subwindow(500, 200)
        print(self.mainwindow.subwindow)
        # self.graphics_layout.addWidget(self.subwindow, 0, 0, 1, 1)
        print(devicewrapper_lst1)
        print(devicewrapper_lst2)
        # self.sub_gui_1 = TimePlotGui(
        #     parent=None,
        #     window=mainwindow,
        #     devicewrapper_lst = devicewrapper_lst1
        # )
        # print('created sub 1 but not sub 2')
        # print(self.subwindow)
        self.sub_gui_2 = TimePlotGui(
            parent=None,
            window= self.mainwindow.subwindow,
            devicewrapper_lst = devicewrapper_lst2
        )
        #self.sub_gui_2.show()
        print('created sub 2')
        # self.sub_gui_1.setFixedSize(QSize(10, 10))
        #self.sub_gui_2.setFixedSize(QSize(500, 30))
        # self.graphics_layout.addWidget(self.sub_gui_1, 0, 0, 1, 1)
        #self.graphics_layout.addWidget(self.sub_gui_2, 1, 1, 1, 1)
        # =====================================================================
        # control buttons - Non-plot widgets (stop/start buttons and spacers) created
        # =====================================================================
        # self.playBtn = QPushButton()
        # self.playBtn.setFixedSize(QSize(30, 30))
        # self.playBtn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        # points = [QPoint(0, 0), QPoint(0, self.playBtn.height()), QPoint(self.playBtn.width(), self.playBtn.height()/2)]
        # self.playBtn.setMask(QRegion(QPolygon(points)))
        # self.playBtn.setStyleSheet("background-color: rgb(120,120,120);")
        #
        # self.squarestopBtn = QPushButton()
        # self.squarestopBtn.setFixedSize(QSize(110, 30))
        # self.squarestopBtn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        # points = [QPoint((self.squarestopBtn.width()+50)/2, 0), \
        #         QPoint((self.squarestopBtn.width()+50)/2, self.squarestopBtn.height()), \
        #         QPoint(self.squarestopBtn.width(), self.squarestopBtn.height()), \
        #         QPoint(self.squarestopBtn.width(), 0)]
        # self.squarestopBtn.setMask(QRegion(QPolygon(points)))
        # self.squarestopBtn.setStyleSheet("background-color: rgb(120,120,120);")
        #
        # self.graphics_layout.addWidget(self.squarestopBtn, 0, 1, 1, 1)
        # self.graphics_layout.addWidget(self.playBtn, 1, 0, 1, 1)

        self.central_wid.setLayout(self.graphics_layout)


    def _set_central_wid_properties(self):
        """ """
        self.central_wid.setAutoFillBackground(True)
        p = self.central_wid.palette()
        p.setColor(self.central_wid.backgroundRole(), QtCore.Qt.darkGray)
        self.central_wid.setPalette(p)

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
        self.time_plot_ui = MultiPanelGui(
            parent=None,
            window=self,
            devicewrapper_lst1=devicewrapper_lst1,
            devicewrapper_lst2=devicewrapper_lst2
        )


    def setGeometry(self, *args, **kwargs):
        """ """
        if len(args) == 0 and len(kwargs) == 0:
            print('here')
            args = PrimaryWindow.DEFAULT_GEOMETRY
        super(PrimaryWindow, self).setGeometry(*args, **kwargs)

    def closeEvent(self, event):
        """ """
        print('event')
        self.time_plot_ui.closeEvent(event)
#        event.accept

    def create_subwindow(self, width, height):
        self.subwindow = SubWindow()
        self.subwindow.create_window(width, height)
        self.subwindow.show()

class SubWindow(QWidget):
    def create_window(self, width, height, parent=None,):
       super(SubWindow,self).__init__(parent)
       self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
       self.resize(width,height)



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

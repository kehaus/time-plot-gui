#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimePlotGui class creates a GUI displaying the time trace of a value from a
given device object




"""

__version__ = "0.0.1"
__author__ = "kha"



import os
from os import path
import ctypes as ct
import numpy as np
import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
from unittest.mock import MagicMock


import sys
import weakref
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QMainWindow
from PyQt5.QtWidgets import qApp, QAction, QMenu, QGridLayout, QLabel, QLineEdit
from PyQt5.QtGui import QIcon, QFont, QCursor
from PyQt5 import QtCore, Qt, QtGui
import pyqtgraph as pg


from time_plot_worker import TimePlotWorker
from plot_item_settings import PlotItemSettings

from util.workerthread import WorkerThread,WorkerTaskBase
from util.devicewrapper import DeviceWrapper, DummyDevice


# ============================================================================
# Excpetion class
# ============================================================================
class TimePlotGuiException(Exception):
    """ """
    pass

# ============================================================================
# TimePlotGui class
# ============================================================================

class TimePlotGui(QWidget):

    start_signal = QtCore.pyqtSignal()
    stop_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None, window=None, devicewrapper=None):
        """ """
        super(TimePlotGui, self).__init__(parent=parent)
        # self.absolute_time = []
        # self.time_array = []
        # self.potential = []
        self.absolute_time = np.array([])
        self.time_array = np.array([])
        self.potential = np.array([])
        self.data = np.array([])
        self._init_ui(window)
        self._init_worker_thread(devicewrapper)


    def _init_ui(self, mainwindow):

        self.central_wid = QWidget(mainwindow)
        self._set_central_wid_properties()
        self.mainwindow = mainwindow
        self.mainwindow.setCentralWidget(self.central_wid)



        # grid layout to put all widgets
        self.wid_layout = QGridLayout()

        # =====================================================================
        # control panel
        # =====================================================================
        self.graphics_layout = QGridLayout()
        self.vl = pg.ValueLabel(formatStr='{avgValue:0.2f} {suffix}')
        self.vl.setStyleSheet("color: white;")
        if len(self.potential) == 0:
            self.vl.setValue(-1)
        else:
            self.vl.setValue(self.potential[-1])
        self.graphics_layout.addWidget(self.vl, 0, 0, 1, 1)


        # =====================================================================
        # control panel
        # =====================================================================
        self.controls_layout = QGridLayout()


        # =====================================================================
        # control buttons - layout
        # =====================================================================
        self.startBtn = QPushButton('START')
        self.controls_layout.addWidget(self.startBtn, 0, 0, 1, 1)
        self.startBtn.setStyleSheet("background-color: white;")
        #self.startBtn.setStyleSheet("color: yellow;")
        self.stopBtn = QPushButton('STOP')
        self.controls_layout.addWidget(self.stopBtn, 1, 0, 1, 1)
        self.stopBtn.setStyleSheet("background-color: white;")

        self.controls_layout.addWidget(self.vl, 0, 1, 1, 1)
        #self.comboBox = QComboBox(self)
        #comboBox.addItem()
        #self.controls_layout.addWidget(self.comboBox, 0, 1, 1, 1)

        self.init_plot()

        # # here we add a button to get the bounds
        # self.default_plot = QPushButton('Get Data Bounds')
        # self.controls_layout.addWidget(self.default_plot, 2, 0, 1, 1)
        # self.default_plot.setStyleSheet("background-color: white;")
        # self.default_plot.clicked.connect(self.getDataBounds)

# Below is the code that creates the buttons for saving/restoring plot settings. I have commented
# it out because I have put that functionality in the context menu
        # self.restore_saved_settings = QPushButton('Restore Saved Plot Settings')
        # self.controls_layout.addWidget(self.restore_saved_settings, 0, 2, 1, 1)
        # self.restore_saved_settings.setStyleSheet("background-color: white;")
        # self.restore_saved_settings.clicked.connect(self.set_custom_settings)
        #
        # # here we add buttons to save or reset defaults
        # self.save_settings = QPushButton('Save Current Settings')
        # self.controls_layout.addWidget(self.save_settings, 4, 0, 1, 1)
        # self.save_settings.setStyleSheet("background-color: white;")
        # self.save_settings.clicked.connect(self.save_current_settings)
        #
        # self.restore_default_settings = QPushButton('Restore Default Plot Settings')
        # self.controls_layout.addWidget(self.restore_default_settings, 5, 0, 1, 1)
        # self.restore_default_settings.setStyleSheet("background-color: white;")
        # self.restore_default_settings.clicked.connect(self.default_settings)

        # =====================================================================
        # control buttons - connections
        # =====================================================================
        self.startBtn.clicked.connect(self.start_thread)
        self.stopBtn.clicked.connect(self.stop_thread)

       # ============================================================
        # put everything together
        # ============================================================
        self.wid_layout.addItem(self.graphics_layout, 0, 4, 6, 6)
        self.wid_layout.addItem(self.controls_layout, 0, 0, 2, 2)
        # self.wid_layout.setColumnStretch(0, 10)
        # self.wid_layout.setColumnStretch(8, 2)

        self.central_wid.setLayout(self.wid_layout)

    def init_plot(self):
        """ """
        print("initializing plot...")
        # if len(self.potential) != 0:
        #     self.graphWidget.removeItem(self.graphItem)
        #     self.graphics_layout.removeWidget(self.graphWidget)
        self.graphWidget = pg.PlotWidget()
        self.graphItem = self.graphWidget.getPlotItem()
        self.viewbox = self.graphItem.getViewBox()
        self.modify_context_menu()
        self.graphics_layout.addWidget(self.graphWidget, 0, 3, 5, 5)
        potential_axis = self.potential
        time_axis = self.time_array
        self.graphItem.setTitle('Potential over Time', **{'color': '#FFF', 'size': '20pt'})
        #self.graphWidget.showAxis('top', False)
        self.graphItem.setLabel('left', 'Potential (Volts)', color='white', size=30)
        self.graphItem.setLabel('bottom', 'Time (seconds)', color='white', size=30)
        self.set_custom_settings()
        self.plotDataItem = self.graphItem.plot(time_axis, potential_axis)

    def set_custom_settings(self):
        self.plot_item_settings = PlotItemSettings()
        # acquires the self.settings varibale from plot_item_settings
        if path.exists(self.plot_item_settings.SETTINGS_FILENAME):
            settings = self.plot_item_settings.settings
        else:
            settings = self.plot_item_settings.DEFAULT_SETTINGS
        self.graphItem.setLogMode(x = settings['xscalelog'], y = settings['yscalelog'])
        self.viewbox.setAutoPan(x = settings['autoPan'])
        self.viewbox.setRange(xRange = settings['xlim'], yRange = settings['ylim'], \
                                disableAutoRange = settings['disableautorange'])

    def save_current_settings(self):
        self.plot_item_settings = PlotItemSettings()
        viewboxstate = self.viewbox.getState()
        #print(f"{viewboxstate}")
        #print(f"{self.graphItem.getScale(x)}")
        self.plot_item_settings.save(xlim = viewboxstate['targetRange'][0],
                                    ylim = viewboxstate['targetRange'][1],
                                    disableautorange = not viewboxstate['autoRange'][0],
                                    autoPan = viewboxstate['autoPan'][0])
        self.set_custom_settings()

    # rename as "restore_default_settings"
    def default_settings(self):
        self.plot_item_settings = PlotItemSettings()
        if path.exists(self.plot_item_settings.settings_filename):
            os.remove(self.plot_item_settings.settings_filename)
        self.set_custom_settings()
        #self.init_plot()

    def modify_context_menu(self):
        self.menu = self.graphItem.getMenu()

        restore_default = QtGui.QAction("Restore Default Plot Settings", self.menu)
        restore_default.triggered.connect(self.default_settings)
        self.menu.addAction(restore_default)
        self.menu.restore_default = restore_default

        restore_saved = QtGui.QAction("Restore Saved Plot Settings", self.menu)
        restore_saved.triggered.connect(self.set_custom_settings)
        self.menu.addAction(restore_saved)
        self.menu.restore_saved = restore_saved

        save_settings = QtGui.QAction("Save Current Plot Settings", self.menu)
        save_settings.triggered.connect(self.save_current_settings)
        self.menu.addAction(save_settings)
        self.menu.save_settings = save_settings

    def getDataBounds(self):
        bounds = self.plotDataItem.dataBounds(0)
        #print(f"{bounds}")
        print('It worked!')

    def _set_central_wid_properties(self):
        """ """
        self.central_wid.setAutoFillBackground(True)
        p = self.central_wid.palette()
        p.setColor(self.central_wid.backgroundRole(), QtCore.Qt.darkGray)
        self.central_wid.setPalette(p)


    def _init_worker_thread(self, devicewrapper):
        """ """

        # Setup QWaitCondition
        self.mutex = QMutex()
        self.cond = QWaitCondition()

        # Setup the measurement engine
#        self.mthread = QtCore.QThread()
        self.worker = TimePlotWorker(devicewrapper, self.mutex, self.cond)


        # connect signal and slots
        self.start_signal.connect(self.worker.start)
        self.stop_signal.connect(self.worker.stop)


        self.worker.reading.connect(self.newReading)

        return


    def start_thread(self):
        self.start_signal.emit()

    def stop_thread(self):
        self.stop_signal.emit()


    def update_ValueLabel(self, val):
        """ """
        self.vl.setValue(val)

        self.update_time_array(val)
        potential_axis = self.potential
        time_axis = self.time_array
        data = self.data
        self.plotDataItem.setData(time_axis, potential_axis)

    def update_time_array(self, val):
        """ """
        #self.potential.append(val)
        self.potential = np.append(self.potential, np.array([val]))
        self.absolute_time = np.append(self.absolute_time, np.array([time.time()]))
        self.time_array = np.array([x - self.absolute_time[0] for x in self.absolute_time])
        self.data = np.append(self.data, np.array([(self.potential[-1], self.time_array[-1])]))


    @QtCore.pyqtSlot(float)
    def newReading(self, val):
        """ """
        pg.QtGui.QApplication.processEvents()
        self.update_ValueLabel(val)
        time.sleep(0.1)         # necessary to avoid worker to freeze
        self.cond.wakeAll()     # wake worker thread up
        return


    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.save_current_settings()
            event.accept()
        else:
            event.ignore()


# ===========================================================================
#
# ===========================================================================

class MainWindow(QMainWindow):
    """ """
    # xpos on screen, ypos on screen, width, height
    DEFAULT_GEOMETRY = [400, 400, 1000, 500]

    def __init__(self, devicewrapper=None):
        super(MainWindow, self).__init__()
        self._init_ui(devicewrapper=devicewrapper)

    def _init_ui(self, window_geometry=None, devicewrapper=None):
        self.setGeometry()
        self.setWindowTitle('time-plot')
        self.setStyleSheet("background-color: black;")
        self.time_plot_ui = TimePlotGui(
            parent=None,
            window=self,
            devicewrapper=devicewrapper
        )

    def setGeometry(self, *args, **kwargs):
        """ """
        if len(args) == 0 and len(kwargs) == 0:
            args = MainWindow.DEFAULT_GEOMETRY
        super(MainWindow, self).setGeometry(*args, **kwargs)

    def closeEvent(self, event):
        """ """
        print('event')
        self.time_plot_ui.closeEvent(event)
#        event.accept


# ===========================================================================
# main function
# ===========================================================================

def main(devicewrapper):
    """ """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print('QApplication instance already exists {}'.format(str(app)))
    window = MainWindow(devicewrapper=devicewrapper)
    window.show()
    app.exec_()


# ===========================================================================
# run main
# ===========================================================================

if __name__ == "__main__":
    dd = DummyDevice()
    dw = DeviceWrapper(dd)

    main(dw)

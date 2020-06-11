#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimePlotGui class creates a GUI displaying the time trace of a value from a
given device object


TODO:
    * implement multi line functionality
    * figure out way to send command to dummy device instead of just gathering data
    * check how to interface the U6



"""

__version__ = "0.0.1"
__author__ = "kha"



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
from PyQt5.QtGui import QIcon, QFont, QCursor, QRegion, QPolygon
from PyQt5 import QtCore, Qt, QtGui
import pyqtgraph as pg


from time_plot_worker import TimePlotWorker
from plot_item_settings import PlotItemSettings, JSONFileHandler

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
    DEFAULT_DATA_FILENAME = 'stored_data.json'

    def __init__(self, parent=None, window=None, devicewrapper_lst=None):
        """ """
        super(TimePlotGui, self).__init__(parent=parent)

        self._create_absolute_time_stamp()

        if type(devicewrapper_lst) == DeviceWrapper:
            devicewrapper_lst = [devicewrapper_lst]
        self.devicewrapper = devicewrapper_lst
        # ===============================
        # Allow for coercion of data and settings to the same number of lines
        # ===============================
        self.started = False
        # ===============================
        # Get the settings object
        # ===============================
        self.plot_item_settings = PlotItemSettings(number_of_lines = len(devicewrapper_lst))
        self.settings = self.plot_item_settings.settings
        self.data_fn = os.path.join(PlotItemSettings.FOLDER_FILENAME, self.DEFAULT_DATA_FILENAME)
        # ===============================
        # Set up the label machine
        # ===============================
        #self.plot_label_machine = PlotLabelMachine()
        #self.label_state = self.plot_label_machine.state

        self._init_ui(window, devicewrapper_lst)
        self._init_multi_worker_thread(devicewrapper_lst)


    def _init_ui(self, mainwindow, devicewrapper_lst):
        """
        Creates and Loads the widgets in the GUI
        """
        # =====================================================================
        # Creates and configures central widget for window
        # =====================================================================
        self.central_wid = QWidget(mainwindow)
        self._set_central_wid_properties()
        self.mainwindow = mainwindow
        self.mainwindow.setCentralWidget(self.central_wid)
        # =====================================================================
        # control panel - initializes layout item to put widgets
        # =====================================================================
        self.graphics_layout = QGridLayout()
        # =====================================================================
        # control buttons - Non-plot widgets (stop/start buttons and spacers) created
        # =====================================================================
        self.playBtn = QPushButton()
        self.playBtn.setFixedSize(QSize(30, 30))
        self.playBtn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        points = [QPoint(0, 0), QPoint(0, self.playBtn.height()), QPoint(self.playBtn.width(), self.playBtn.height()/2)]
        self.playBtn.setMask(QRegion(QPolygon(points)))
        self.playBtn.setStyleSheet("background-color: rgb(120,120,120);")

        self.squarestopBtn = QPushButton()
        self.squarestopBtn.setFixedSize(QSize(110, 30))
        self.squarestopBtn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        points = [QPoint((self.squarestopBtn.width()+50)/2, 0), \
                QPoint((self.squarestopBtn.width()+50)/2, self.squarestopBtn.height()), \
                QPoint(self.squarestopBtn.width(), self.squarestopBtn.height()), \
                QPoint(self.squarestopBtn.width(), 0)]
        self.squarestopBtn.setMask(QRegion(QPolygon(points)))
        self.squarestopBtn.setStyleSheet("background-color: rgb(120,120,120);")

        self.blankWidget = QWidget()
        self.blankWidget.setFixedSize(QSize(500, 30))

        self.blankWidget2 = QWidget()
        self.blankWidget2.setFixedSize(QSize(30, 30))
        # =====================================================================
        # Initialize the plot
        # =====================================================================
        self._init_plot(devicewrapper_lst)
        # =====================================================================
        # Add Widgets to layout, including the Plot itself. Note that the order
        # in which these are added matters because several widgets overlap.
        # =====================================================================
        self.graphics_layout.addWidget(self.blankWidget, 0, 2)
        self.graphics_layout.addWidget(self.blankWidget2, 0, 1)
        self.graphics_layout.addWidget(self.graphWidget, 0, 0, 5, 4)
        self.graphics_layout.addWidget(self.squarestopBtn, 0, 0)
        self.graphics_layout.addWidget(self.playBtn, 0, 0)
        # =====================================================================
        # control buttons - connections
        # =====================================================================
        self.playBtn.clicked.connect(self.thread_status_changed)
        self.playBtn.clicked.connect(self.start_thread)
        self.squarestopBtn.clicked.connect(self.stop_thread)
        # ============================================================
        # Assign layout widget to window
        # ============================================================
        self.central_wid.setLayout(self.graphics_layout)


    def _init_plot(self, devicewrapper_lst):
        """ """
        # ===============================
        # Initializes plot by generating the plotWidget, plotItem, and ViewBox objects that are callable
        # ===============================
        self.graphWidget = pg.PlotWidget()
        self.graphItem = self.graphWidget.getPlotItem()
        self.viewbox = self.graphItem.getViewBox()
        # ===============================
        # Enable Automatic Axis Label Updates
        # ===============================
        self.graphItem.ctrl.fftCheck.stateChanged.connect(self.change_label_state)
        # # ===============================
        # # Zoom lines created
        # # ===============================
        # self.left_bound = pg.InfiniteLine(movable=True, angle=90, label='x={value:0.2f}',
        #                labelOpts={'position':0.1, 'color': (200,0,0), 'fill': (200,200,200,50), 'movable': True})
        # self.right_bound = pg.InfiniteLine(movable=True, angle=90, label='x={value:0.2f}',
        #                labelOpts={'position':0.1, 'color': (200,0,0), 'fill': (200,200,200,50), 'movable': True})
        # self.upper_bound = pg.InfiniteLine(movable=True, angle=0, label='y={value:0.2f}',
        #                labelOpts={'position':0.1, 'color': (200,0,0), 'fill': (200,200,200,50), 'movable': True})
        # self.lower_bound = pg.InfiniteLine(movable=True, angle=0, label='y={value:0.2f}',
        #                labelOpts={'position':0.1, 'color': (200,0,0), 'fill': (200,200,200,50), 'movable': True})
        # # ===============================
        # # Zoom lines added to graphWidget
        # # ===============================
        # self.graphWidget.addItem(self.left_bound)
        # self.graphWidget.addItem(self.right_bound)
        # self.graphWidget.addItem(self.upper_bound)
        # self.graphWidget.addItem(self.lower_bound)
        # # ===============================
        # # Zoom lines connected to changing bounds
        # # ===============================
        # self.upper_bound.sigPositionChanged.connect(self.ammend_y_bounds)
        # self.lower_bound.sigPositionChanged.connect(self.ammend_y_bounds)
        # self.right_bound.sigPositionChanged.connect(self.ammend_x_bounds)
        # self.left_bound.sigPositionChanged.connect(self.ammend_x_bounds)
        # ===============================
        # initlialize data lines
        # ===============================
        self._init_data_items(devicewrapper_lst)
        self._align_time_stamps()
        # ===============================
        # Customize the context menu
        # ===============================
        self._modify_context_menu()
        # ===============================
        # customize plot settings with stored values
        # ===============================
        self.set_custom_settings()


    def _init_data_items(self, devicewrapper_lst, new_data = None):
        self.data_table = {}
        #for id_nr, dw in enumerate(devicewrapper_lst):
        #for id_nr in range(len(self.settings['line_settings'])):
        id_nr = 0
        while True:
            data_item = TimePlotDataItem(id_nr=id_nr, absolute_time=self.t0)
            if new_data is None:
                data_item.recall_data(self.data_fn)
            elif new_data is not None:
                data_item.recall_data(new_data)
            if len(data_item.get_plot_data_item().xData) == 0:
                break
            self.data_table.update(
                {id_nr: data_item}
            )
            self.graphItem.addItem(data_item.get_plot_data_item())
            id_nr += 1


    def _create_absolute_time_stamp(self):
        self.t0 = time.time()

    def reset_absolute_time_stamp(self):
        self.t0 = time.time()

    def _align_time_stamps(self):
        """compares and aligns time stamps between TimePlotGui and data_items"""

        if not hasattr(self, 'data_table'):
            raise TimePlotGuiException(
                'data_table variable not present. Call init_data_items() first'
            )

        # define the TimePlotGui absolute_time to be the earliest time stemp present
        t0_lst = [
            data_item.absolute_time for data_item in self.data_table.values()
        ]
        self.t0 = min(t0_lst + [self.t0])

        # shift times in data_item object in respect to TimePlotGui absolute_time
        for data_item in self.data_table.values():
            if not np.isclose(self.t0, data_item.absolute_time, rtol=1e-3):
                dt = data_item.absolute_time - self.t0
                t,y = data_item.get_data()
                data_item.set_data(t+dt, y)
                data_item.absolute_time = self.t0

    def thread_status_changed(self):
        self.started = not self.started
        self.resize_line_settings()
        self.add_line_settings_menu()

    def resize_line_settings(self):
        if self.started:
            self.coerce_same_length(data_length = len(self.devicewrapper))
            self.resize_data_table()
        else:
            self.coerce_same_length(data_length = len(self.data_table))

    def resize_data_table(self):
        while len(self.devicewrapper) != len(self.data_table):
            if len(self.devicewrapper) > len(self.data_table):
                id_nr = len(self.data_table)
                data_item = TimePlotDataItem(id_nr=id_nr, absolute_time=self.t0)
                self.data_table.update(
                    {id_nr: data_item}
                )
                self.graphItem.addItem(data_item.get_plot_data_item())
            elif len(self.devicewrapper) < len(self.data_table):
                timeplotdataitem = self.data_table[max(self.data_table.keys())]
                self.graphItem.removeItem(self.data_table[max(self.data_table.keys())].get_plot_data_item())
                del timeplotdataitem
                self.data_table.popitem()


    def coerce_same_length(self, data_length):
        while data_length != len(self.settings['line_settings']):
            if data_length > len(self.settings['line_settings']):
                self.settings['line_settings'][str(len(self.settings['line_settings']))] = \
                            self.plot_item_settings.default_line_settings
            elif data_length < len(self.settings['line_settings']):
                self.settings['line_settings'].popitem()


    def set_custom_settings(self, label_key = 'potential'):
        # ===============================
        # Set all of the parameters accoringing to the settings parameters
        # ===============================
        self.graphItem.setLogMode(x = self.settings['xscalelog'], y = self.settings['yscalelog'])
        self.graphItem.showGrid(x = self.settings['xgridlines'], y = self.settings['ygridlines'], \
                                alpha = self.settings['gridopacity'])
        for key in self.data_table:
            time_data_item = self.data_table[key]
            data_item = time_data_item.get_plot_data_item()
            data_item.setAlpha(alpha = self.settings['line_settings'][str(key)]['line_alpha'], auto = False)
            data_item.setPen(pg.mkPen(width = self.settings['line_settings'][str(key)]['line_width'], \
                            color = self.settings['line_settings'][str(key)]['line_color']))
            data_item.setFftMode(self.settings['frequency_state'])
        #self.plotDataItem.setAlpha(alpha = self.settings['plotalpha'][0], auto = self.settings['plotalpha'][1])
        self.viewbox.setAutoPan(x = self.settings['autoPan'])
        self.viewbox.setRange(xRange = self.settings['xlim'], yRange = self.settings['ylim'])
        self.viewbox.enableAutoRange(x = self.settings['xautorange'], y = self.settings['yautorange'])
        self.data_options.automatic_clear_checkbox.setChecked(self.settings['auto_clear_data'])
        self.viewbox.setMouseEnabled(x = self.settings['x_zoom'], y = self.settings['y_zoom'])
        if self.settings['mouseMode'] == 1:
            self.viewbox.setLeftButtonAction(mode = 'rect')
        else:
            self.viewbox.setLeftButtonAction(mode = 'pan')
        self.frequency_state = self.settings['frequency_state']
        self.graphItem.ctrl.fftCheck.setChecked(self.frequency_state)
        # self.left_bound.setValue(self.settings['zoom_lines'][0])
        # self.right_bound.setValue(self.settings['zoom_lines'][1])
        # self.lower_bound.setValue(self.settings['zoom_lines'][2])
        # self.upper_bound.setValue(self.settings['zoom_lines'][3])
        # ===============================
        # Assign axis labels accordingly
        # ===============================
        self.update_plot_labels()

    # def set_labels(self):
    #     #self.label_state = PlotLabelMachine().state
    #     if self.counter not in globals():
    #         self.counter = int(self.settings['time_state'])
    #     if self.counter % 2 == 1:
    #         self.set_time_labels()
    #     else:
    #         self.set_frequency_labels()
    #     counter += 1
    def update_plot_labels(self):
        if self.frequency_state:
            self.set_frequency_labels()
        else:
            self.set_time_labels()

    def change_label_state(self):
        self.frequency_state = not self.frequency_state
        self.update_plot_labels()

    def set_frequency_labels(self, key = 'potential'):
        labels = self.get_axis_labels(key)
        title = 'Fourier Transform of ' + labels['title']
        self.graphItem.setTitle(title, **{'color': '#FFF', 'size': '20pt'})
        self.graphItem.setLabel('left', 'Amplitude', color='white', size=30)
        self.graphItem.setLabel('bottom', 'Frequency', color='white', size=30)

    def set_time_labels(self, key = 'potential'):
        labels = self.get_axis_labels(key)
        self.graphItem.setTitle(labels['title'], **{'color': '#FFF', 'size': '20pt'})
        self.graphItem.setLabel('left', labels['y_label'], color='white', size=30)
        self.graphItem.setLabel('bottom', labels['x_label'], color='white', size=30)

    def get_axis_labels(self, key = 'potential'):
        sample_labels = {
                'temp':         {'x_label':     "Time (Seconds)",
                                'y_label':      "Temperature (K)"},
                'potential':    {'x_label':     "Time (Seconds)",
                                'y_label':      "Potential (Volts)"},
                'pressure':     {'x_label':     "Time (Seconds)",
                                'y_label':      "Pressure (kPa)"}
        }
        labels = {
                'x_label':  '',
                'y_label':  '',
                'title':    ''
        }
        labels['x_label'] = sample_labels[key]['x_label']
        labels['y_label'] = sample_labels[key]['y_label']
        labels['title'] = labels['x_label'] + ' 0ver ' + labels['y_label']
        if self.settings['xscalelog']:
            labels['x_label'] += '\n(Log Scale)'
        if self.settings['yscalelog']:
            labels['y_label'] += '\n(Log Scale)'
        return labels

    def save_current_settings(self):
        # ===============================
        # Get Viewbox so both viewbox and PlotItem (self.graphItem) parameters are accessible
        # ===============================
        viewboxstate = self.viewbox.getState()
        # ===============================
        # Save setting: Line settings
        # ===============================
        self.save_line_settings()
        # ===============================
        # Save setting: All other settings
        # ===============================
        self.plot_item_settings.save_settings(
            autoPan = viewboxstate['autoPan'][0],
            xscalelog = self.graphItem.ctrl.logXCheck.isChecked(),
            yscalelog = self.graphItem.ctrl.logYCheck.isChecked(),
            xlim = viewboxstate['targetRange'][0],
            ylim = viewboxstate['targetRange'][1],
            xautorange = viewboxstate['autoRange'][0],
            yautorange = viewboxstate['autoRange'][1],
            xgridlines = self.graphItem.ctrl.xGridCheck.isChecked(),
            ygridlines = self.graphItem.ctrl.yGridCheck.isChecked(),
            gridopacity = self.graphItem.ctrl.gridAlphaSlider.value()/255,
            plotalpha = self.graphItem.alphaState(),
            mouseMode = viewboxstate['mouseMode'],
            x_zoom = viewboxstate['mouseEnabled'][0],
            y_zoom = viewboxstate['mouseEnabled'][0],
            auto_clear_data = self.data_options.automatic_clear_checkbox.isChecked(),
            frequency_state = False
            #frequency_state = self.graphItem.ctrl.fftCheck.isChecked()
            # zoom_lines = self.get_zoom_lines()
        )

    def restore_default_settings(self):
        # ===============================
        # Delete stored file settings
        # ===============================
        if path.exists(self.plot_item_settings.settings_filename):
            os.remove(self.plot_item_settings.settings_filename)
        # ===============================
        # Delete PlotItemSettings instance and create new one
        # ===============================
        del self.plot_item_settings
        self.plot_item_settings = PlotItemSettings(number_of_lines = len(self.devicewrapper))
        self.settings = self.plot_item_settings.DEFAULT_SETTINGS
        self.resize_line_settings()
        # ===============================
        # Implement the settings
        # ===============================
        self.ammend_context_menu()
        self.set_custom_settings()

    def _modify_context_menu(self):
        self.resize_line_settings()
        # ===============================
        # Get the context menu as a callable object
        # ===============================
        self.menu = self.graphItem.getMenu()
        # ===============================
        # Create submenus (in order)
        # ===============================
        self.line_settings_menu = self.menu.addMenu("Line Settings")
        self.visualization_settings = self.menu.addMenu("Visualization Settings")
        self.data_options = self.menu.addMenu("Data Options")
        # ===============================
        # Submenu Formation: line_settings
        # ===============================
        self.add_line_settings_menu()
        # ===============================
        # Submenu Formation: visualization_settings
        # ===============================
        restore_default = QtGui.QAction("Restore Default Plot Settings", self.visualization_settings)
        restore_default.triggered.connect(self.restore_default_settings)
        self.visualization_settings.addAction(restore_default)
        self.visualization_settings.restore_default = restore_default

        restore_saved = QtGui.QAction("Restore Saved Plot Settings", self.visualization_settings)
        restore_saved.triggered.connect(self.set_custom_settings)
        self.visualization_settings.addAction(restore_saved)
        self.visualization_settings.restore_saved = restore_saved

        save_settings = QtGui.QAction("Save Current Plot Settings", self.visualization_settings)
        save_settings.triggered.connect(self.save_current_settings)
        self.visualization_settings.addAction(save_settings)
        self.visualization_settings.save_settings = save_settings
        # ===============================
        # Submenu Formation: Data Options
        # ===============================
        clear_data = QtGui.QAction("Clear Data", self.data_options)
        clear_data.triggered.connect(self.clear_all_data)
        self.data_options.addAction(clear_data)
        self.data_options.clear_data = clear_data

        automatic_clear = QtGui.QWidgetAction(self.data_options)
        automatic_clear_checkbox = QtGui.QCheckBox("Automatically Clear Data", self)
        automatic_clear.setDefaultWidget(automatic_clear_checkbox)
        automatic_clear_checkbox.stateChanged.connect(self.save_data_settings)
        self.data_options.addAction(automatic_clear)
        self.data_options.automatic_clear = automatic_clear
        self.data_options.automatic_clear_checkbox = automatic_clear_checkbox
        # ===============================
        # Function Formation: Load Past Data
        # ===============================
        open_data = QtGui.QAction("Load Stored Data")
        open_data.triggered.connect(self.open_finder)
        self.menu.addAction(open_data)
        self.menu.open_data = open_data
        # # ===============================
        # # Function Formation: Set Zoom lines
        # # ===============================
        # get_zoom_lines = QtGui.QAction("Zoom Lines")
        # get_zoom_lines.triggered.connect(self.set_zoom_lines)
        # self.menu.addAction(get_zoom_lines)
        # self.menu.get_zoom_lines = get_zoom_lines
        # ===============================
        # Remove unnecesary default context menu operations
        # ===============================
        actions = self.graphItem.ctrlMenu.actions()
        for index in [1, 2, 5]:
            self.graphItem.ctrlMenu.removeAction(actions[index])

    def ammend_context_menu(self):
        alpha_sliders = self.line_settings_menu.actions()[1::4]
        width_sliders = self.line_settings_menu.actions()[2::4]
        key = 0
        for slider in alpha_sliders:
            slider.defaultWidget().setValue(self.settings['line_settings'][str(key)]['line_alpha']*255)
            key += 1
        key = 0
        for slider in width_sliders:
            slider.defaultWidget().setValue(self.settings['line_settings'][str(key)]['line_width']*255)
            key += 1

    def add_line_settings_menu(self):
        # ===============================
        # remove existing items from the menu
        # ===============================
        self.line_settings_menu.clear()
        # ===============================
        # Submenu Formation: line_settings
        # ===============================
        for key in self.data_table:
            # ===============================
            # title
            # ===============================
            title = QtGui.QAction('Line ' + str(key), self.line_settings_menu)
            title.setEnabled(False)
            self.line_settings_menu.addAction(title)
            self.line_settings_menu.title = title
            # ===============================
            # alpha
            # ===============================
            alpha = QtGui.QWidgetAction(self.line_settings_menu)
            alphaSlider = QtGui.QSlider(self.line_settings_menu)
            alphaSlider.setOrientation(QtCore.Qt.Horizontal)
            alphaSlider.setMaximum(255)
            alphaSlider.setValue(self.settings['line_settings'][str(key)]['line_alpha']*255)
            alphaSlider.valueChanged.connect(self.data_table[key].setAlpha)
            alpha.setDefaultWidget(alphaSlider)
            self.line_settings_menu.addAction(alpha)
            self.line_settings_menu.alpha = alpha
            self.line_settings_menu.alphaSlider = alphaSlider
            # ===============================
            # width
            # ===============================
            width = QtGui.QWidgetAction(self.line_settings_menu)
            widthSlider = QtGui.QSlider(self.line_settings_menu)
            widthSlider.setOrientation(QtCore.Qt.Horizontal)
            widthSlider.setMaximum(2550)
            widthSlider.setMinimum(255)
            widthSlider.setValue(self.settings['line_settings'][str(key)]['line_width']*255)
            widthSlider.valueChanged.connect(self.data_table[key].setWidth)
            width.setDefaultWidget(widthSlider)
            self.line_settings_menu.addAction(width)
            self.line_settings_menu.width = width
            self.line_settings_menu.widthSlider = widthSlider
            # # ===============================
            # # width
            # # ===============================
            # widthintermediate = QtGui.QWidgetAction(self.line_settings_menu)
            # widthbox = QtGui.QInputDialog(self.line_settings_menu)
            # widthbox.NoButtons
            # widthintermediate.setDefaultWidget(widthbox)
            # self.line_settings_menu.addAction(widthintermediate)
            # self.line_settings_menu.widthintermediate = widthintermediate
            # self.line_settings_menu.widthbox = widthbox
            # ===============================
            # color
            # ===============================
            change_line_color = QtGui.QAction("Change Line Color", self.line_settings_menu)
            change_line_color.triggered.connect(self.data_table[key].open_color_dialog)
            self.line_settings_menu.addAction(change_line_color)
            self.line_settings_menu.change_line_color = change_line_color

    # ===============================
    # The Following functions are unused unless the zoom lines are re-added
    # ===============================
    def set_zoom_lines(self):
        multiplier1 = 0.0376562
        multiplier2 = 0.03099
        self.upper_bound.setValue(self.viewbox.getState()['targetRange'][1][1]- \
            multiplier1*(self.viewbox.getState()['targetRange'][1][1]- self.viewbox.getState()['targetRange'][1][0]))
        self.lower_bound.setValue(self.viewbox.getState()['targetRange'][1][0]+ \
            multiplier1*(self.viewbox.getState()['targetRange'][1][1]- self.viewbox.getState()['targetRange'][1][0]))
        self.right_bound.setValue(self.viewbox.getState()['targetRange'][0][1]- \
            multiplier1*(self.viewbox.getState()['targetRange'][0][1]- self.viewbox.getState()['targetRange'][0][0]))
        self.left_bound.setValue(self.viewbox.getState()['targetRange'][0][0]+ \
            multiplier1*(self.viewbox.getState()['targetRange'][0][1]- self.viewbox.getState()['targetRange'][0][0]))

    def get_zoom_lines(self):
        return [self.left_bound.getXPos(), self.right_bound.getXPos(), \
                self.lower_bound.getYPos(), self.upper_bound.getYPos()]

    def ammend_bounds(self):
        self.viewbox.setRange(xRange = [self.left_bound.getXPos(), self.right_bound.getXPos()],
                            yRange = [self.lower_bound.getYPos(), self.upper_bound.getYPos()])

    def ammend_x_bounds(self):
        self.viewbox.setXRange(max = self.right_bound.getXPos(), min = self.left_bound.getXPos())

    def ammend_y_bounds(self):
        self.viewbox.setYRange(max = self.upper_bound.getYPos(), min = self.lower_bound.getYPos())
    # ===============================
    # (end of obsolete functions... the below functions are used)
    # ===============================

    def open_finder(self):
        self.started = False
        data_fname = QFileDialog.getOpenFileName(self, 'Open file', '~/',"JSON files (*.json)")
        settings_fname = QFileDialog.getOpenFileName(self, 'Open file', '~/',"JSON files (*.json)")
        if settings_fname[0] !='':
            del self.plot_item_settings
            self.plot_item_settings = PlotItemSettings(unusal_settings_file = settings_fname[0])
        if data_fname[0] is not None:
            self.clear_all_plot_data_items()
            self._init_data_items(self.devicewrapper, new_data = data_fname[0])
            self._modify_context_menu()
            self.set_custom_settings()

    def clear_all_plot_data_items(self):
        data_items = self.graphItem.listDataItems()
        for data_item in data_items:
            self.graphItem.removeItem(data_item)

    def save_data_settings(self):
        self.plot_item_settings.save_settings( \
            auto_clear_data = self.data_options.automatic_clear_checkbox.isChecked())

    def save_line_settings(self):
        alpha_sliders = self.line_settings_menu.actions()[1::4]
        width_sliders = self.line_settings_menu.actions()[2::4]
        number = 0
        for slider in alpha_sliders:
            self.settings['line_settings'][str(number)]['line_alpha'] = slider.defaultWidget().value()/255
            number += 1
        number = 0
        for slider in width_sliders:
            self.settings['line_settings'][str(number)]['line_width'] = slider.defaultWidget().value()/255
            number += 1

    def store_all_data(self):
        """
        **inehrits store_current_data function to adjust for multi-line-plotting**

        """
        frequency_state = self.frequency_state
        self.graphItem.ctrl.fftCheck.setChecked(False)
        if path.exists(self.data_fn):
            os.remove(self.data_fn)
        for data_item in self.data_table.values():
            data_item.store_data(fn=self.data_fn)
        self.graphItem.ctrl.fftCheck.setChecked(frequency_state)

    def clear_all_data(self):
        """
        **inherits clear_current_data function to adjust for multi-line-plotting**
        """
        self.reset_absolute_time_stamp()
        for data_item in self.data_table.values():
            data_item.clear_data()
            data_item.reset_absolute_time(absolute_time=self.t0)


    def _set_central_wid_properties(self):
        """ """
        self.central_wid.setAutoFillBackground(True)
        p = self.central_wid.palette()
        p.setColor(self.central_wid.backgroundRole(), QtCore.Qt.darkGray)
        self.central_wid.setPalette(p)


    def _init_multi_worker_thread(self, devicewrapper_lst):
        """initializes a worker thread for every devicewrapper"""

        # set up QWaitCondition
        self.mutex_table = {
            idx: QMutex() for idx in range(len(devicewrapper_lst))
        }
        self.cond_table = {
            idx: QWaitCondition() for idx in range(len(devicewrapper_lst))
        }

        # set up the measurement engine
        self.worker_table = {}
        for idx, devicewrapper in enumerate(devicewrapper_lst):
            worker = TimePlotWorker(
                devicewrapper,
                self.mutex_table[idx],
                self.cond_table[idx],
                id_nr=idx
            )

            # connect signal and slot
            worker.reading.connect(self.newReading)
            self.start_signal.connect(worker.start)
            self.stop_signal.connect(worker.stop)

            self.worker_table.update({idx: worker})


    def start_thread(self):
        if self.data_options.automatic_clear_checkbox.isChecked():
            self.graphItem.ctrl.fftCheck.setChecked(False)
            self.clear_all_data()
        self.start_signal.emit()

    def stop_thread(self):
        self.stop_signal.emit()

    def update_datapoint(self, id_nr, val):
        """updates TimePlotDataItem object with corresponding to id_nr"""
        frequency_state = self.frequency_state
        self.graphItem.ctrl.fftCheck.setChecked(False)
        self.data_table[id_nr].add_value(val)
        self.graphItem.ctrl.fftCheck.setChecked(frequency_state)
        #self.set_zoom_lines()

    # def __del__(self):
    #     print('it worked!?')
    #     #super(self, TimePlotGui).__del__()


    @QtCore.pyqtSlot(int, float)
    def newReading(self, id_nr, val):
        """ """
        pg.QtGui.QApplication.processEvents()
        self.update_datapoint(id_nr, val)
        time.sleep(0.01)         # necessary to avoid worker to freeze
        self.cond_table[id_nr].wakeAll()     # wake worker thread up
        return

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.save_current_settings()
            self.store_all_data()
            event.accept()
        else:
            event.ignore()



# ===========================================================================
# helper classes
# ===========================================================================

class PlotDataItemV2(pg.PlotDataItem):
    """Child class customizes pyqtgraph.PlotDataItem

    This child class is designed to act as replacement for a PlotDataItem class
    and should therefore be able to neatlessly interface with the other
    pyqtgraph plot objects (e.g. ViewBox, PlotItem, PlotWidget)

    This class overwrites:
        * _fourierTransform-function: fixes bug which caused indexing error



    """

    def _fourierTransform(self, x, y):
        """Perform fourier transform. If x values are not sampled uniformly,
        then use np.interp to resample before taking fft.
        """
        #self.plot_label_machine.switch_event('fourier')
        dx = np.diff(x)
        uniform = not np.any(np.abs(dx-dx[0]) > (abs(dx[0]) / 1000.))
        if not uniform:
            x2 = np.linspace(x[0], x[-1], len(x))
            y = np.interp(x2, x, y)
            x = x2
        f = np.fft.fft(y) / len(y)
        y = abs(f[1:int(len(f)/2)])
        dt = x[-1] - x[0]
        x = np.linspace(0, 0.5*len(x)/dt, len(y))
        return x, y

class PlotLabelMachine():
    """ """

    def __init__(self, time_state = True):
        if time_state:
            self.state = TimeState()
        else:
            self.state = FrequencyState()

    def switch_event(self, text = None):
        return self.state.switch_state(text)

class FrequencyState(PlotLabelMachine):
    """ """

    def switch_state(self, text):
        if text is None or 'time' in text:
            return TimeState()

class TimeState(PlotLabelMachine):
    """ """

    def switch_state(self, text):
        if text is None or 'fourier' in text:
            return FrequencyState()


# ===========================================================================
# helper class - Data item
# ===========================================================================
class TimePlotDataItem(JSONFileHandler):
    """wraps the pq.PlotDataItem class to extend functionality

    Main functionality enhancement is that PlotDataItem data can now be
    extended by providing a single value. Internal functionality will take care
    of generating corresponding time value and appending the the Data object of
    PlotCurveItem.
    Furthermore, this class provides loading and saving capabilities for
    storing data in json files.


    TO INCLUDE:
        * automatic saving mechanism

    """

    DATA_NAME = 'data_{:d}'

    def __init__(self, id_nr=0, absolute_time=None):
        self.id_nr = id_nr
        self.data_name = self._compose_data_name()
        self.pdi = PlotDataItemV2([],[])
        if absolute_time == None:
            self.absolute_time = time.time()
        else:
            self.absolute_time = absolute_time

    def _compose_data_name(self):
        return TimePlotDataItem.DATA_NAME.format(self.id_nr)

    def reset_absolute_time(self, absolute_time):
        self.absolute_time = absolute_time

    def get_plot_data_item(self):
        """returns the pg.PlotDataItem"""
        return self.pdi

    def add_value(self, val):
        """adds value to pg.PlotDataItem data array"""
        t, y = self.pdi.getData()
        t = np.append(t, time.time() - self.absolute_time)
        y = np.append(y, val)
        self.pdi.setData(t,y)

    def get_data(self):
        """returns the pg.PlotDataItem time and data arrays"""
        return self.pdi.getData()

    def set_data(self, *args, **kwargs):
        """replaces data with provided data"""
        self.pdi.setData(*args, **kwargs)

    def clear_data(self):
        """clears all data present in this data object"""
        self.pdi.setData([],[])

    def store_data(self, fn):
        """saves data as nested dictionary in json file"""

        # extract data from PlotDataItem object
        t, y = self.get_data()
        t = t.tolist(); y = y.tolist()
        data_dct = {
            't': t,
            'y': y,
            'absolute_time': self.absolute_time
        }

        # load all data, update and overwrite existing file to avoid
        #   json-format corruption.
        if path.exists(fn):
            all_data_dct = self.load(fn)
        else:
            all_data_dct = {}

        all_data_dct.update({self.data_name:data_dct})
        self.save(fn, all_data_dct, mode='w')
        return

    def recall_data(self, fn):
        """checks for data in data file and updates pq.PlotDataItem object if
        present
        """
        if path.exists(fn):
            all_data_dct = self.load(fn)
        else:
            all_data_dct = {}

        if self.data_name in all_data_dct.keys():
            data_dct = all_data_dct[self.data_name]
            t = data_dct['t']
            y = data_dct['y']
            self.absolute_time = data_dct['absolute_time']
            self.set_data(t,y)
        return

    def setAlpha(self, value):
        self.pdi.setAlpha(value/255, False)

    def setWidth(self, value):
        self.pdi.setPen(pg.mkPen(width = value/255))

    def open_color_dialog(self):
        color_dialog = QColorDialog.getColor()
        self.pdi.setPen(pg.mkPen(color = color_dialog.getRgb()))


# class TimePlotDataTable(JSONFileHandler):
#     """ """

#     DEFAULT_DATA_FILENAME = 'data.json'

#     def __init__(self, data_fn=None):

#         if data_fn == None:
#             self.fn = TimePlotDataTable.DEFUALT_DATA_FILENAME

# ===========================================================================
#
# ===========================================================================
class MainWindow(QMainWindow):
    """ """
    # xpos on screen, ypos on screen, width, height
    DEFAULT_GEOMETRY = [400, 400, 1000, 500]

    def __init__(self, devicewrapper_lst=None):
        super(MainWindow, self).__init__()
        self._init_ui(devicewrapper_lst=devicewrapper_lst)

    def _init_ui(self, window_geometry=None, devicewrapper_lst=None):
        self.setGeometry()
        self.setWindowTitle('time-plot')
        self.setStyleSheet("background-color: black;")
        self.time_plot_ui = TimePlotGui(
            parent=None,
            window=self,
            devicewrapper_lst=devicewrapper_lst
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
def main(devicewrapper_lst):
    """ """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print('QApplication instance already exists {}'.format(str(app)))
    window = MainWindow(devicewrapper_lst=devicewrapper_lst)
    try:
        window.show()
        app.exec_()
    except:
        window.closeEvent()
    # window.show()
    # app.exec_()


# ===========================================================================
# run main
# ===========================================================================

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

    main([dw1, dw2, dw3])

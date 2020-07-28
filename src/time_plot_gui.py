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
import datetime
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition, QSize, QPoint
from unittest.mock import MagicMock


import sys
import weakref
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QMainWindow, QHBoxLayout
from PyQt5.QtWidgets import qApp, QAction, QMenu, QGridLayout, QLabel, QLineEdit, QSizePolicy, QFileDialog
from PyQt5.QtWidgets import QInputDialog, QColorDialog, QSpinBox, QGraphicsWidget, QComboBox, QDialog
from PyQt5.QtGui import QIcon, QFont, QCursor, QRegion, QPolygon, QWindow, QColor
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
    pause_signal = QtCore.pyqtSignal()
    restart_signal = QtCore.pyqtSignal()
    DEFAULT_DATA_FILENAME = 'stored_data.json'

    def __init__(self, parent=None, window=None, devicewrapper_lst=None, folder_filename = None, sampling_latency = .01):
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
        self.start_button_counter = 0
        # ===============================
        # Allow customization of delay between samples
        # ===============================
        self.sampling_latency = sampling_latency
        # ===============================
        # Get the settings object
        # ===============================
        self.plot_item_settings = PlotItemSettings(number_of_lines = len(devicewrapper_lst), folder_filename = folder_filename)
        self.settings = self.plot_item_settings.settings
        self.data_fn = os.path.join(self.plot_item_settings.folder_filename, self.DEFAULT_DATA_FILENAME)
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
        # self.mainwindow = mainwindow
        # self.mainwindow.setCentralWidget(self.central_wid)
        # if isinstance(self.mainwindow, MainWindow) or isinstance(self.mainwindow, SubWindow):
        #     self.mainwindow.setCentralWidget(self.central_wid)
        # else:
        #     print('else case')
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

        # self.pauseBtn = QPushButton()
        # self.restartBtn = QPushButton()
        # self.pauseBtn.setStyleSheet("background-color: rgb(120,120,120);")
        # self.restartBtn.setStyleSheet("background-color: rgb(120,120,120);")
        # self.graphics_layout.addWidget(self.pauseBtn, 0, 6, 1, 1)
        # self.pauseBtn.clicked.connect(self.pause_thread)
        # self.graphics_layout.addWidget(self.restartBtn, 1, 6, 1, 1)
        # self.restartBtn.clicked.connect(self.restart_thread)
        # =====================================================================
        # control buttons - connections
        # =====================================================================
        self.playBtn.clicked.connect(self.save_line_settings)
        self.playBtn.clicked.connect(self.thread_status_changed)
        self.playBtn.clicked.connect(self.start_thread)
        self.squarestopBtn.clicked.connect(self.pause_thread)

        print(self.graphItem.titleLabel)
        # # self.graphItem.titleLabel.setAcceptedMouseButtons()
        # # self.graphItem.titleLabel.clicked.connect(self.change_title)
        # self.clicked_signal = pg.GraphicsScene.sigMouseClicked
        # print(self.clicked_signal)
        # self.clicked_signal.connect(self.change_title)
        # # self.clicked_signal.connect(self.change_title)
        # ============================================================
        # Assign layout widget to window
        # ============================================================
        self.central_wid.setLayout(self.graphics_layout)


    def _init_plot(self, devicewrapper_lst):
        """ """
        # ===============================
        # Initializes plot by generating the plotWidget, plotItem, and ViewBox objects that are callable
        # ===============================
        self.graphWidget = pg.PlotWidget(axisItems = \
            {'bottom': TimeAxisItem(orientation='bottom', t0 = self.t0, relative_time = self.settings['relative_timestamp'])})
        self.graphItem = self.graphWidget.getPlotItem()
        self.viewbox = self.graphItem.getViewBox()

        # self.barrier = PlotDataItemV2([],[])
        # self.graphItem.addItem(self.barrier)
        # ===============================
        # Enable Automatic Axis Label Updates
        # ===============================
        self.graphItem.ctrl.fftCheck.stateChanged.connect(self.change_label_state)
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
            data_item = TimePlotDataItem(data_fn = self.data_fn, id_nr=id_nr, absolute_time=self.t0)
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
            # print(len(self.devicewrapper))
            self.coerce_same_length(data_length = len(self.devicewrapper))
            # print(len(self.data_table))
            self.resize_data_table()
            # print(len(self.data_table))
        else:
            self.coerce_same_length(data_length = len(self.data_table))
        self.set_line_settings()

    def resize_data_table(self):
        # print('resizing data table')
        while len(self.devicewrapper) != len(self.data_table):
            if len(self.devicewrapper) > len(self.data_table):
                id_nr = len(self.data_table)
                data_item = TimePlotDataItem(data_fn = self.data_fn, id_nr=id_nr, absolute_time=self.t0)
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

    def traditional_times(self):
        traditional_time_array = []
        time_array, y = self.data_table[0].get_data()
        for entry in time_array:
            print(entry)
            print(time.asctime(time.localtime(entry + self.t0)))
            test = int(time.mktime(datetime.datetime.now().timetuple()))
            print(f"now: {test} \n {type(test)}")
            final = datetime.datetime.fromtimestamp(test).strftime("%H:%M")
            print(type(datetime.datetime.fromtimestamp(test)))
            print(f"final: {final}")
            test_b = time.mktime(time.localtime(entry + self.t0))
            print(test_b)
            test_b_final = datetime.datetime.fromtimestamp(int(test_b)).strftime("%H:%M")
            print(test_b_final)
            traditional_time_array.append(time.asctime(time.localtime(entry + self.t0)))
        # for value in self.data_table.values():
        #     print(value)
        #     time_array, y = self.data_table[0].get_data()
        #     value.set_data(traditional_time_array, y)

    def set_custom_settings(self, label_key = 'potential'):
        # ===============================
        # Set all of the parameters accoringing to the settings parameters
        # ===============================
        self.graphItem.setLogMode(x = self.settings['xscalelog'], y = self.settings['yscalelog'])
        self.graphItem.showGrid(x = self.settings['xgridlines'], y = self.settings['ygridlines'], \
                                alpha = self.settings['gridopacity'])
        self.set_line_settings()
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
        # ===============================
        # Assign axis labels accordingly
        # ===============================
        self.update_plot_labels()

    def set_line_settings(self):
        for key in self.data_table:
            time_data_item = self.data_table[key]
            data_item = time_data_item.get_plot_data_item()
            data_item.setAlpha(alpha = self.settings['line_settings'][str(key)]['line_alpha'], auto = False)
            data_item.setPen(pg.mkPen(width = self.settings['line_settings'][str(key)]['line_width'], \
                            color = self.settings['line_settings'][str(key)]['line_color']))
            data_item.setFftMode(self.settings['frequency_state'])

    def update_plot_labels(self):
        if self.frequency_state:
            self.set_frequency_labels()
        else:
            self.set_time_labels()

    def change_label_state(self):
        self.frequency_state = self.graphItem.ctrl.fftCheck.isChecked()
        self.update_plot_labels()

    def set_frequency_labels(self, key = 'potential'):
        labels = self.get_axis_labels(key)
        title = 'Fourier Transform of ' + labels['title']
        title_font_size = str(self.settings['labels']['title_font_size']) + 'pt'
        x_font_size = str(self.settings['labels']['x_axis_font_size']) + 'pt'
        y_font_size = str(self.settings['labels']['y_axis_font_size']) + 'pt'
        self.graphItem.setTitle(title, **{'color': '#FFF', 'size': title_font_size})
        self.graphItem.setLabel('left', 'Amplitude', **{'color': '#FFF', 'font-size': y_font_size})
        self.graphItem.setLabel('bottom', 'Frequency',  **{'color': '#FFF', 'font-size': x_font_size})

    def set_time_labels(self, key = 'potential'):
        labels = self.get_axis_labels(key)
        title_font_size = str(self.settings['labels']['title_font_size']) + 'pt'
        x_font_size = str(self.settings['labels']['x_axis_font_size']) + 'pt'
        y_font_size = str(self.settings['labels']['y_axis_font_size']) + 'pt'
        self.graphItem.setTitle(labels['title'], **{'color': '#FFF', 'size': title_font_size})
        self.graphItem.setLabel('left', labels['y_label'], **{'color': '#FFF', 'font-size': y_font_size})
        self.graphItem.setLabel('bottom', labels['x_label'], **{'color': '#FFF', 'font-size': x_font_size})

    def get_axis_labels(self, key = 'potential'):
        # sample_labels = {
        #         'temp':         {'x_label':     "Time (Seconds)",
        #                         'y_label':      "Temperature (K)"},
        #         'potential':    {'x_label':     "Time (Seconds)",
        #                         'y_label':      "Potential (Volts)"},
        #         'pressure':     {'x_label':     "Time (Seconds)",
        #                         'y_label':      "Pressure (kPa)"}
        # }
        labels = {
                'x_label':  '',
                'y_label':  '',
                'title':    ''
        }
        # labels['x_label'] = sample_labels[key]['x_label']
        # labels['y_label'] = sample_labels[key]['y_label']
        labels['x_label'] = self.settings['labels']['x_axis_data_type'] + " (" + self.settings['labels']['x_axis_unit'] + ")"
        labels['y_label'] = self.settings['labels']['y_axis_data_type'] + " (" + self.settings['labels']['y_axis_unit'] + ")"
        if self.settings['labels']['title_text'] is None:
            labels['title'] = labels['x_label'] + ' 0ver ' + labels['y_label']
        else:
            labels['title'] = self.settings['labels']['title_text']
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
            # frequency_state = False
            frequency_state = self.graphItem.ctrl.fftCheck.isChecked(),
            labels = self.settings['labels']
        )

    def restore_default_settings(self):
        temp_line_settings = self.settings['line_settings']
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
        self.settings['line_settings'] = temp_line_settings
        self.resize_line_settings()
        # ===============================
        # Implement the settings
        # ===============================
        self.ammend_context_menu()
        self.set_custom_settings()

    def clear_line_settings(self):
        self.settings['line_settings'] = self.plot_item_settings.DEFAULT_SETTINGS['line_settings']
        self.set_line_settings()
        self.ammend_context_menu()

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
        self.change_labels_menu = self.menu.addMenu("Change Labels")
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

        clear_line_settings = QtGui.QAction("Clear Line Settings", self.visualization_settings)
        clear_line_settings.triggered.connect(self.clear_line_settings)
        self.visualization_settings.addAction(clear_line_settings)
        self.visualization_settings.clear_line_settings = clear_line_settings
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
        # Submenu Formation: Change Labels
        # ===============================
        change_title = QtGui.QAction("Change Plot Title", self.change_labels_menu)
        change_title.triggered.connect(self.change_title)
        self.change_labels_menu.addAction(change_title)
        self.change_labels_menu.change_title = change_title

        change_x_axis_label = QtGui.QAction("Change X Axis Label", self.change_labels_menu)
        change_x_axis_label.triggered.connect(self.change_x_axis_label)
        self.change_labels_menu.addAction(change_x_axis_label)
        self.change_labels_menu.change_x_axis_label = change_x_axis_label

        change_y_axis_label = QtGui.QAction("Change Y Axis Label", self.change_labels_menu)
        change_y_axis_label.triggered.connect(self.change_y_axis_label)
        self.change_labels_menu.addAction(change_y_axis_label)
        self.change_labels_menu.change_y_axis_label = change_y_axis_label
        # ===============================
        # Function Formation: Load Past Data
        # ===============================
        open_data = QtGui.QAction("Load Stored Data")
        open_data.triggered.connect(self.open_finder)
        self.menu.addAction(open_data)
        self.menu.open_data = open_data
        # ===============================
        # Submenu revision: local fourier transform
        # ===============================
        self.transform_menu = self.menu.actions()[0].menu()

        local_fourier = QtGui.QWidgetAction(self.transform_menu)
        local_fourier_widget = QWidget()
        lf_label = QLabel("Local Fourier Mode")
        local_fourier_checkbox = QtGui.QCheckBox(self)
        local_fourier_checkbox.stateChanged.connect(self.set_local_ft_mode)
        lf_layout = QHBoxLayout()
        lf_layout.addWidget(lf_label)
        lf_layout.addWidget(local_fourier_checkbox)
        local_fourier_widget.setLayout(lf_layout)
        local_fourier.setDefaultWidget(local_fourier_widget)
        self.transform_menu.addAction(local_fourier)
        self.transform_menu.local_fourier = local_fourier

        # transform_menu_actions = self.transform_menu.actions()
        # print(transform_menu_actions)
        # for index in range(len(transform_menu_actions)):
        #     self.transform_menu.removeAction(transform_menu_actions[index])
        # for index in [1, 0]:
        #     self.transform_menu.addAction(transform_menu_actions[index])


        traditional_times = QtGui.QAction("traditional time")
        traditional_times.triggered.connect(self.traditional_times)
        self.menu.addAction(traditional_times)
        self.menu.traditional_times = traditional_times

        # ===============================
        # Remove unnecesary default context menu operations
        # ===============================
        actions = self.graphItem.ctrlMenu.actions()
        #1,2,3,5
        for index in range(len(actions)):
            self.graphItem.ctrlMenu.removeAction(actions[index])
        # actions = self.graphItem.ctrlMenu.actions()
        # self.graphItem.ctrlMenu.clear()
        for index in [0, 4, 6, 7, 8, 9, 10, 11]:
            self.graphItem.ctrlMenu.addAction(actions[index])

    def ammend_context_menu(self):
        line_controls = self.line_settings_menu.actions()[0::2]
        key = 0
        for line in line_controls:
            line.defaultWidget().layout().itemAt(2).widget().setValue(255*self.settings['line_settings'][str(key)]['line_alpha'])
            line.defaultWidget().layout().itemAt(4).widget().setValue(self.settings['line_settings'][str(key)]['line_width'])
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
            # width and alpha
            # ===============================
            mainlabel = QLabel('Line '+str(key))
            mainlabel.setAlignment(QtCore.Qt.AlignCenter)
            widthintermediate = QtGui.QWidgetAction(self.line_settings_menu)
            width_widget = QtGui.QWidget()
            widthlabel = QLabel("Line Width:")
            spinbox = QSpinBox()
            spinbox.setValue(self.settings['line_settings'][str(key)]['line_width'])
            spinbox.setRange(1, 15)
            spinbox.setSingleStep(1)

            alphalabel = QLabel("Alpha")
            alphaSlider = QtGui.QSlider(self.line_settings_menu)
            alphaSlider.setOrientation(QtCore.Qt.Horizontal)
            alphaSlider.setMaximum(255)
            alphaSlider.setValue(self.settings['line_settings'][str(key)]['line_alpha']*255)

            width_layout = QGridLayout()
            width_layout.addWidget(mainlabel, 0, 0, 1, 2)
            width_layout.addWidget(alphalabel, 1, 0, 1, 1)
            width_layout.addWidget(alphaSlider, 1, 1, 1, 1)
            width_layout.addWidget(widthlabel, 2, 0, 1, 1)
            width_layout.addWidget(spinbox, 2, 1, 1, 1)
            width_widget.setLayout(width_layout)
            # width_widget.setStyleSheet("border-bottom: 1px solid")

            spinbox.valueChanged.connect(self.data_table[key].setWidth)
            alphaSlider.valueChanged.connect(self.data_table[key].setAlpha)
            widthintermediate.setDefaultWidget(width_widget)
            self.line_settings_menu.addAction(widthintermediate)
            self.line_settings_menu.widthintermediate = widthintermediate
            # ===============================
            # color
            # ===============================
            change_line_color = QtGui.QWidgetAction(self.line_settings_menu)
            color_button = QPushButton("Change line color")
            color_button.clicked.connect(self.data_table[key].open_color_dialog)
            change_line_color.setDefaultWidget(color_button)
            self.line_settings_menu.addAction(change_line_color)
            self.line_settings_menu.change_line_color = change_line_color


    def open_finder(self):
        self.started = False
        data_fname = QFileDialog.getOpenFileName(self, 'Open file', '~/',"JSON files (*.json)")
        if data_fname[0] !='':
            settings_fname = QFileDialog.getOpenFileName(self, 'Open file', '~/',"JSON files (*.json)")
            # print(settings_fname)
            if settings_fname[0] !='':
                del self.plot_item_settings
                self.plot_item_settings = PlotItemSettings(unusal_settings_file = settings_fname[0])
                self.settings = self.plot_item_settings.settings
                # print(self.settings)
            if data_fname[0] is not None:
                self.clear_all_plot_data_items()
                self._init_data_items(self.devicewrapper, new_data = data_fname[0])
                self.resize_line_settings()
                self.add_line_settings_menu()
                self.set_custom_settings()
                # self.ammend_context_menu()

    def set_local_ft_mode(self):
        """starts or stops the local FT mode depending on local fourier checkbox
        state
        """
        if self.transform_menu.local_fourier.defaultWidget().layout().itemAt(1).widget().isChecked():
            if not self.graphItem.ctrl.fftCheck.isChecked():
                for dataitem in self.data_table.values():
                    dataitem.start_local_ft_mode()
                    print('%%%%%% started local fourier mode')
            else:
                self.transform_menu.local_fourier.defaultWidget().layout().itemAt(1).widget().setChecked(False)
                self.local_ft_error()
        else:
            for dataitem in self.data_table.values():
                dataitem.stop_local_ft_mode()
                print('%%%%%% stopped local fourier mode')
        return

    def clear_all_plot_data_items(self):
        data_items = self.graphItem.listDataItems()
        for data_item in data_items:
            self.graphItem.removeItem(data_item)

    def save_data_settings(self):
        self.plot_item_settings.save_settings( \
            auto_clear_data = self.data_options.automatic_clear_checkbox.isChecked())

    def save_line_settings(self):
        line_controls = self.line_settings_menu.actions()[0::2]
        number = 0
        for line in line_controls:
            self.settings['line_settings'][str(number)]['line_alpha'] = line.defaultWidget().layout().itemAt(2).widget().value()/255
            self.settings['line_settings'][str(number)]['line_width'] = line.defaultWidget().layout().itemAt(4).widget().value()
            number += 1
        for key in range(len(self.data_table)):
            self.settings['line_settings'][str(key)]['line_color'] = \
                self.data_table[key].get_plot_data_item().get_color()
        self.plot_item_settings.save_settings(line_settings = self.settings['line_settings'])

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

    def change_title(self):
        title, acccepted = QInputDialog.getText(self, 'Change Title',
                                        'Enter New Title:')
        if acccepted:
            self.graphItem.setTitle(title)
            self.settings['labels']['title_text'] = title

    def change_x_axis_label(self):
        axis_label, acccepted = QInputDialog.getText(self, 'Change Title',
                                        'Enter New Title:')
        if acccepted:
            self.graphItem.setLabel('bottom', axis_label)
            self.settings['labels']['x_axis_data_type'] = axis_label
        dialog = QDialog()
        dialog.open()

    def change_y_axis_label(self):
        axis_label, acccepted = QInputDialog.getText(self, 'Change Title',
                                        'Enter New Title:')
        if acccepted:
            self.graphItem.setLabel('left', axis_label)
            self.settings['labels']['y_axis_data_type'] = axis_label

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
            self.pause_signal.connect(worker.pause)
            self.restart_signal.connect(worker.restart)

            self.worker_table.update({idx: worker})

    def leaving_fft_mode(self):
        mode_change_popup = QMessageBox()
        mode_change_popup.setText("You are exiting FFT Transform mode and entering Time Dependence mode." \
            "If you would like to re-enter FFT Transform mode, you may do so from the context menu.")
        mode_change_popup.setIcon(QMessageBox.Information)
        mode_change_popup.exec_()

    def local_ft_error(self):
        local_ft_error = QMessageBox()
        local_ft_error.setText("You are already in FFT mode. If you would like a local transform," \
            "please select a region in Time Dependence mode.")
        local_ft_error.setIcon(QMessageBox.Information)
        local_ft_error.exec_()


    def start_thread(self):
        if self.start_button_counter == 0:
            self.start_button_counter += 1
            is_checked = False
            if self.data_options.automatic_clear_checkbox.isChecked():
                if self.graphItem.ctrl.fftCheck.isChecked():
                    is_checked = True
                self.graphItem.ctrl.fftCheck.setChecked(False)
                self.clear_all_data()
            # elif not self.data_options.automatic_clear_checkbox.isChecked() \
            #             and len(self.data_table[0].get_plot_data_item().getData()[0]) != 0:
            #     barrier_data_x, barrier_data_y = self.barrier.getData()
            #     barrier_data_x = np.append(barrier_data_x, self.data_table[0].get_plot_data_item().getData()[0][-1])
            #     barrier_data_y = np.append(barrier_data_y, self.data_table[0].get_plot_data_item().getData()[1][-1])
            #     self.barrier.setData(barrier_data_x, barrier_data_y)
            # print(self.data_table)
            # for key in self.data_table:
            #     print(type(key))
            #     print(self.data_table[key])
            self.start_signal.emit()
            if is_checked:
                self.leaving_fft_mode()
            # print(self.data_table)
        else:
            self.restart_thread()

    def pause_thread(self):
        self.stop_thread()
        # self.pause_signal.emit()

    def restart_thread(self):
        self.restart_signal.emit()

    def stop_thread(self):
        # self.restart_signal.emit()
        # time.sleep(2)
        self.stop_signal.emit()

    def update_datapoint(self, id_nr, val, time_val):
        """updates TimePlotDataItem object with corresponding to id_nr"""
        frequency_state = self.frequency_state
        self.graphItem.ctrl.fftCheck.setChecked(False)
        self.data_table[id_nr].add_value(val, time_val)
        self.graphItem.ctrl.fftCheck.setChecked(frequency_state)
        # if len(self.barrier.getData()[0]) == 1 and id_nr == 0:
        #     barrier_data_x, barrier_data_y = self.barrier.getData()
        #     barrier_data_x = np.append(barrier_data_x, time_val - self.t0)
        #     barrier_data_y = np.append(barrier_data_y, val)
        #     self.barrier.setData(barrier_data_x, barrier_data_y)
        #     self.barrier.setPen(pg.mkPen(style=QtCore.Qt.DotLine, width = 10, color = (255,80,10,255)))
        #self.set_zoom_lines()

    # def __del__(self):
    #     print('it worked!?')
    #     #super(self, TimePlotGui).__del__()


    @QtCore.pyqtSlot(int, float, float)
    def newReading(self, id_nr, val, time_val):
        """ """
        pg.QtGui.QApplication.processEvents()
        # print(id_nr)
        # print(self.data_table)
        self.update_datapoint(id_nr, val, time_val)
        time.sleep(self.sampling_latency)
        # time.sleep(0.01)         # necessary to avoid worker to freeze
        self.cond_table[id_nr].wakeAll()     # wake worker thread up
        return

    def closeEvent(self, event, auto_accept = False):
        """
        By default, this function generates a pop-up confirming you want to close the gui before running
        closing protocol. This pop-up can be overridden with the auto_accept argument which is espcially
        useful in avoiding mulitple redundant popups in large gui with multiple TimePlotGui objects.
        """
        if not auto_accept:
            reply = QMessageBox.question(self, 'Message',
                "Are you sure to quit?", QMessageBox.Yes |
                QMessageBox.No, QMessageBox.Yes)

            if reply == QMessageBox.Yes:
                self.accept_close_event(event)
            else:
                event.ignore()
                return False
        else:
            self.accept_close_event(event)
            return True

    def accept_close_event(self, event):
        """This runs all of the standard protocol for closing the GUI properly"""
        self.save_current_settings()
        self.store_all_data()
        self.stop_thread()
        event.accept()


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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.opts.update({
            'fftLocal':     False
        })

    def getData(self):
        if self.xData is None:
            return (None, None)

        if self.xDisp is None:
            x = self.xData
            y = self.yData


            if self.opts['fftMode']:
                if self.opts['fftLocal']:
                    x,y = self._get_data_in_local_ft_boundaries(x,y)
                x,y = self._fourierTransform(x, y)
                # Ignore the first bin for fft data if we have a logx scale
                if self.opts['logMode'][0]:
                    x=x[1:]
                    y=y[1:]

            if self.opts['logMode'][0]:
                x = np.log10(x)
            if self.opts['logMode'][1]:
                y = np.log10(y)

            ds = self.opts['downsample']
            if not isinstance(ds, int):
                ds = 1

            if self.opts['autoDownsample']:
                # this option presumes that x-values have uniform spacing
                range = self.viewRect()
                if range is not None:
                    dx = float(x[-1]-x[0]) / (len(x)-1)
                    x0 = (range.left()-x[0]) / dx
                    x1 = (range.right()-x[0]) / dx
                    width = self.getViewBox().width()
                    if width != 0.0:
                        ds = int(max(1, int((x1-x0) / (width*self.opts['autoDownsampleFactor']))))
                    ## downsampling is expensive; delay until after clipping.

            if self.opts['clipToView']:
                view = self.getViewBox()
                if view is None or not view.autoRangeEnabled()[0]:
                    # this option presumes that x-values have uniform spacing
                    range = self.viewRect()
                    if range is not None and len(x) > 1:
                        dx = float(x[-1]-x[0]) / (len(x)-1)
                        # clip to visible region extended by downsampling value
                        x0 = np.clip(int((range.left()-x[0])/dx)-1*ds , 0, len(x)-1)
                        x1 = np.clip(int((range.right()-x[0])/dx)+2*ds , 0, len(x)-1)
                        x = x[x0:x1]
                        y = y[x0:x1]

            if ds > 1:
                if self.opts['downsampleMethod'] == 'subsample':
                    x = x[::ds]
                    y = y[::ds]
                elif self.opts['downsampleMethod'] == 'mean':
                    n = len(x) // ds
                    x = x[:n*ds:ds]
                    y = y[:n*ds].reshape(n,ds).mean(axis=1)
                elif self.opts['downsampleMethod'] == 'peak':
                    n = len(x) // ds
                    x1 = np.empty((n,2))
                    x1[:] = x[:n*ds:ds,np.newaxis]
                    x = x1.reshape(n*2)
                    y1 = np.empty((n,2))
                    y2 = y[:n*ds].reshape((n, ds))
                    y1[:,0] = y2.max(axis=1)
                    y1[:,1] = y2.min(axis=1)
                    y = y1.reshape(n*2)


            self.xDisp = x
            self.yDisp = y
        return self.xDisp, self.yDisp

    def _get_data_in_local_ft_boundaries(self, x, y):
        """truncates x and y to values displayed in correspinding viewbox """
        # get viebox x limits
        if not hasattr(self, '_local_ft_xmin') or not hasattr(self, '_local_ft_xmax'):
            self.start_local_ft_mode()
        xmin, xmax = self._local_ft_xmin, self._local_ft_xmax
        print('************* xmin: ', xmin)
        print('************* xmin: ', xmax)

        # truncate x and y
        idx_lst = (xmin<x) & (x<xmax)
        x_, y_ = x[idx_lst], y[idx_lst]
        return x_,y_

    def _get_viewbox_boundaries(self):
        vb = self.getViewBox()
        vbstate = vb.getState()
        xmin, xmax = vbstate['targetRange'][0]
        return xmin, xmax

    def set_local_ft_boundaries(self, xmin, xmax):
        self._local_ft_xmin = xmin
        self._local_ft_xmax = xmax

    def start_local_ft_mode(self):
        xmin, xmax = self._get_viewbox_boundaries()
        self.set_local_ft_boundaries(xmin, xmax)
        self.opts['fftLocal'] = True

    def stop_local_ft_mode(self):
        self.opts['fftLocal'] = False

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

    def get_color(self):
        return self.opts['pen'].color().getRgb()

    def update_width(self, value):
        # /255
        self.opts['pen'].setWidth(value)
        self.updateItems()

    def update_color(self, color_dialog):
        if type(color_dialog) is QColor:
            self.opts['pen'].setColor(color_dialog)
        else:
            self.opts['pen'].setColor(color_dialog.currentColor())
        self.updateItems()

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

class TimeAxisItem(pg.AxisItem):
    def __init__(self, t0, relative_time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t0 = t0
        self.relative_time = relative_time
        self.setLabel(text='Time', units=None)
        self.enableAutoSIPrefix(False)

    def tickStrings(self, values, scale, spacing):
        if self.logMode:
            return self.logTickStrings(values, scale, spacing)

        places = max(0, np.ceil(-np.log10(spacing*scale)))
        strings = []
        for v in values:
            vs = v * scale
            if abs(vs) < .001 or abs(vs) >= 10000:
                vstr = "%g" % vs
            else:
                vstr = ("%%0.%df" % places) % vs
            strings.append(vstr)
        if self.relative_time:
            return strings
        else:
            return [datetime.datetime.fromtimestamp(int(time.mktime(time.localtime(value + self.t0)))).strftime("%H:%M:%S") for value in values]


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

    def __init__(self, data_fn, id_nr=0, absolute_time=None):
        self.id_nr = id_nr
        self.data_name = self._compose_data_name()
        self.data_fn = data_fn
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

    def add_value(self, val, time_val):
        """adds value to pg.PlotDataItem data array"""
        t, y = self.pdi.getData()
        t = np.append(t, time_val - self.absolute_time)
        y = np.append(y, val)
        self.pdi.setData(t,y)
        if len(t)%30 == 0:
            self.store_data(self.data_fn)

    def get_data(self):
        """returns the pg.PlotDataItem time and data arrays"""
        return self.pdi.getData()

    def set_data(self, *args, **kwargs):
        """replaces data with provided data"""
        self.pdi.setData(*args, **kwargs)

    def clear_data(self):
        """clears all data present in this data object"""
        self.pdi.setData([],[])

    def start_local_ft_mode(self):
        self.pdi.start_local_ft_mode()

    def stop_local_ft_mode(self):
        self.pdi.stop_local_ft_mode()

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
        self.pdi.update_width(value)
        # self.pdi.setPen(pg.mkPen(width = value/255))

    def open_color_dialog(self):
        # self.restorable_color = self.pdi.get_color()
        self.restorable_color = self.pdi.opts['pen'].color()
        self.color_dialog = QtGui.QColorDialog()
        self.color_dialog.currentColorChanged.connect(self.set_color)
        self.color_dialog.rejected.connect(self.cancel_color_dialog)
        self.color_dialog.open()
        # self.pdi.setPen(pg.mkPen(color = color_dialog.getRgb()))
        # print(self.pdi.opts['pen'])
        #self.pdi.update_color(self.color_dialog)
        # print(self.pdi.opts['pen'])
        # self.pdi.setPen(self.pdi.opts['pen'])

    def set_color(self):
        self.pdi.update_color(self.color_dialog)
    #     self.pdi.opts['pen'].setColor(color_dialog.currentColor())
    #     self.pdi.setPen(self.pdi.opts['pen'])

    def cancel_color_dialog(self):
        self.pdi.update_color(self.restorable_color)

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
            devicewrapper_lst=devicewrapper_lst,
            folder_filename = None
        )
        self.test_widget = QWidget()
        self.layout = QGridLayout()
        self.setCentralWidget(self.test_widget)
        self.layout.addWidget(self.time_plot_ui.central_wid, 0, 0, 1, 1)
        self.test_widget.setLayout(self.layout)


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

    main([dw1, dw2])
    # app = QApplication.instance()
    # if app is None:
    #     app = QApplication(sys.argv)
    # else:
    #     print('QApplication instance already exists {}'.format(str(app)))
    # window = MainWindow(devicewrapper_lst=[dw1, dw2])
    # try:
    #     window.show()
    #     app.exec_()
    # except:
    #     window.closeEvent()

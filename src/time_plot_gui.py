#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimePlotGui class creates a GUI displaying the time trace of a value from a
given device object


TODO:
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
from PyQt5.QtWidgets import QInputDialog, QColorDialog, QSpinBox, QGraphicsWidget, QComboBox, QDialog, QAbstractSpinBox
from PyQt5.QtGui import QIcon, QFont, QCursor, QRegion, QPolygon, QWindow, QColor
from PyQt5 import QtCore, Qt, QtGui
import pyqtgraph as pg


try:
    from .time_plot_worker import TimePlotWorker
    from .plot_item_settings import PlotItemSettings, JSONFileHandler


    from .util.workerthread import WorkerThread,WorkerTaskBase
    from .util.devicewrapper import DeviceWrapper, DummyDevice
    from .viewboxv2 import ViewBoxV2
    from .time_plot_data_item import TimePlotDataItem
    from .time_axis_item import TimeAxisItem
    from .context_menu import TimePlotContextMenu
except:
    from time_plot_worker import TimePlotWorker
    from plot_item_settings import PlotItemSettings, JSONFileHandler

    from util.workerthread import WorkerThread,WorkerTaskBase
    from util.devicewrapper import DeviceWrapper, DummyDevice
    from viewboxv2 import ViewBoxV2
    from time_plot_data_item import TimePlotDataItem
    from time_axis_item import TimeAxisItem
    from context_menu import TimePlotContextMenu


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
    """ 
    QWidget collects and displays data in line plot item in real time
    
    
    Parameters
    ----------
    parent : QWidget
        PyQt handle to introduce inheritance dependence
    window : QWidget, QMainWindow
        specifies QWidget in which TimePlotgui will be placed
    devices : lst, DeviceWrapper object
        DeviceWrapper objects handle hardware communication 
    folder_filename : str
        directory where  plot settings and plot data will be stored
    sampling_latency : float
        time delay between two sample acquistion
    
    
    """
    
    DEFAULT_DATA_FILENAME = 'stored_data.json'

    start_signal = QtCore.pyqtSignal()
    stop_signal = QtCore.pyqtSignal()
    pause_signal = QtCore.pyqtSignal()
    restart_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None, window=None, devices=None, 
                 folder_filename = None, sampling_latency = .005):
        super(TimePlotGui, self).__init__(parent=parent)
        self._create_absolute_time_stamp()
        self.dev_lst = self._check_devices_type(devices)
        self.dev_num = len(self.dev_lst)
        self.sampling_latency = sampling_latency
        
        # ===============================
        # Allow for coercion of data and settings to the same number of lines
        # ===============================
        self.started = False
        self.start_button_counter = 0
        self.previous_x_max = None
        self.previous_y_max = None
        # ===============================
        # setup gui and worker thread
        # ===============================
        self._init_settings(folder_filename)
        self._init_ui(window, self.dev_lst)
        self._init_multi_worker_thread(devices)


    def _init_ui(self, mainwindow, dev_lst):
        """
        Creates the ui layout and initializes all the necessary QWidget components
        
        Parameter
        ---------
        mainwindow : QMainWindow, QWidget
            QWidget which will be used as central_widget for TimePlotGui
        dev_lst : lst
            lst of DeviceWrapper object used to collect data
            
            
        """
        # =====================================================================
        # Creates and configures central widget for window
        # =====================================================================
        self.central_wid = QWidget(mainwindow)
        self._set_central_wid_properties()
        # =====================================================================
        # control panel - initializes layout item to put widgets
        # =====================================================================
        self.graphics_layout = QGridLayout()
        # =====================================================================
        # control buttons - Non-plot widgets (stop/start buttons and spacers)
        # =====================================================================
        self.playBtn = QPushButton()
        self.playBtn.setFixedSize(QSize(30, 30))
        self.playBtn.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        )
        points = [
            QPoint(0, 0), 
            QPoint(0, self.playBtn.height()), 
            QPoint(self.playBtn.width(), self.playBtn.height()/2)
        ]
        self.playBtn.setMask(QRegion(QPolygon(points)))
        self.playBtn.setStyleSheet("background-color: rgb(120,120,120);")

        self.stopBtn = QPushButton()
        self.stopBtn.setFixedSize(QSize(110, 30))
        self.stopBtn.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        )
        points = [
            QPoint((self.stopBtn.width()+50)/2, 0),
            QPoint((self.stopBtn.width()+50)/2, self.stopBtn.height()),
            QPoint(self.stopBtn.width(), self.stopBtn.height()),
            QPoint(self.stopBtn.width(), 0)
        ]
        self.stopBtn.setMask(QRegion(QPolygon(points)))
        self.stopBtn.setStyleSheet("background-color: rgb(120,120,120);")

        self.blankWidget = QWidget()
        self.blankWidget.setFixedSize(QSize(500, 30))

        self.blankWidget2 = QWidget()
        self.blankWidget2.setFixedSize(QSize(30, 30))
        # =====================================================================
        # Initialize the plot
        # =====================================================================
        self._init_plot(dev_lst)
        # =====================================================================
        # Add Widgets to layout, including the Plot itself. Note that the order
        # in which these are added matters because several widgets overlap.
        # =====================================================================
        self.graphics_layout.addWidget(self.blankWidget, 0, 2)
        self.graphics_layout.addWidget(self.blankWidget2, 0, 1)
        self.graphics_layout.addWidget(self.graphWidget, 0, 0, 5, 4)
        self.graphics_layout.addWidget(self.stopBtn, 0, 0)
        self.graphics_layout.addWidget(self.playBtn, 0, 0)

        # =====================================================================
        # control buttons - connections
        # =====================================================================
        self.playBtn.clicked.connect(self.save_line_settings)
        self.playBtn.clicked.connect(self.thread_status_changed)
        self.playBtn.clicked.connect(self.start_thread)
        self.stopBtn.clicked.connect(self.pause_thread)
        # ============================================================
        # Assign layout widget to window
        # ============================================================
        self.central_wid.setLayout(self.graphics_layout)


    def _init_plot(self, dev_lst):
        """Initializes plot item by customizing corresponding Widgets
        
        This function initializes the plot item by customizing the pyqtgraph
        objects like *PlotWidget*, *PlotItem*, and *ViewBox*.
        
        Parameter
        ---------
        dev_lst : lst
            lst of DeviceWrapper object used to collect data
        
        """

        try:
            self.viewbox = ViewBoxV2()
            self.graphItem = pg.PlotItem(viewBox = self.viewbox)
            self.axis_item = TimeAxisItem(
                orientation='bottom', 
                t0 = self.t0, 
                relative_time = self.settings['relative_timestamp']
            )
            self.graphWidget = pg.PlotWidget(
                axisItems={'bottom': self.axis_item}, 
                plotItem=self.graphItem
            )
        except:
            print("ERROR with custom viewbox class. 'Except' case run instead.")
            self.graphWidget = pg.PlotWidget(
                axisItems={'bottom': self.axis_item}
            )
            self.graphItem = self.graphWidget.getPlotItem()
            self.viewbox = self.graphItem.getViewBox()
        # ===============================
        # Enable Automatic Axis Label Updates
        # ===============================
        self.graphItem.ctrl.fftCheck.stateChanged.connect(self.change_label_state)
        # ===============================
        # initlialize data lines
        # ===============================
        self._init_data_table(dev_lst)
        self._align_time_stamps()
        # ===============================
        # Customize the context menu
        # ===============================
        menu = self.graphItem.getMenu()
        viewbox_menu = self.graphItem.getViewBox().getMenu(True)
        self.context_menu = TimePlotContextMenu(menu, viewbox_menu, self)
        # self._modify_context_menu()
        # ===============================
        # customize plot settings with stored values
        # ===============================
        self.set_custom_settings()


    def _init_data_table(self, dev_lst, new_data = None):
        """initialize data table by populating it with data items
        
        data items are initialized from scratch or loaded from file
        
        Parameter
        ---------
        dev_lst : lst
            lst of DeviceWrapper object used to collect data
        new_data :  **??**
            **??**
            
        """
        self.data_table = {}
        
        id_nr = 0
        while True:
            # data_item = TimePlotDataItem(
            #     data_fn = self.data_fn, 
            #     id_nr=id_nr, 
            #     absolute_time=self.t0
            # )
            data_item = self._create_data_item(id_nr)
            if new_data is None:
                data_item.recall_data(self.data_fn)
                
            else:
                data_item.recall_data(new_data)
            # if len(data_item.get_plot_data_item().xData) == 0:
            if len(data_item.get_time_data()) == 0:
                break
            # self.data_table.update(
            #     {id_nr: data_item}
            # )
            # self.graphItem.addItem(data_item.get_plot_data_item())
            self._add_data_item(id_nr, data_item)
            id_nr += 1
            
    def _init_settings(self, folder_filename):
        """initialize plot settings
        
        Settings are initialized by loading from file or from default values. 
        To initialize the plot settingsa PlotItemSettings object is created.
        
        Parameters
        ----------
        folder_filename : str
            path to settings filename
            
        
        """
        self.plot_item_settings = PlotItemSettings(
            number_of_lines=self.dev_num, 
            folder_filename=folder_filename
        )
        self.settings = self.plot_item_settings.settings
        self.data_fn = os.path.join(
            self.plot_item_settings.folder_filename, 
            self.DEFAULT_DATA_FILENAME
        )
        return
        

    def _check_devices_type(self, devices):
        """checks devices and reformats if necessary
        
        Function is used to allow TimePlotGui initialization with either one 
        devicewrapper object or a list of devicewrapper objects. Function 
        returns a list of device wrappres
        
        Parameters
        ----------
        devices : DeviceWrapper object or list of DeviceWrapper objects
            DeviceWrapper object handle hardware communication
            
        Returns
        -------
        lst
            list of DeviceWrapper object
        
        Raises
        ------
        TimePlotGuiException
            if devices contains variables which are not of type DeviceWrapper
        
        """
        err_msg = """
        Given devices are not of type DeviceWrapper. 
        Make sure that elemnts in devices are DeviceWrapper and initialize 
        TimePlotGui again.
        """
        
        if type(devices) is DeviceWrapper:
            return [devices]
        if all([type(d) is DeviceWrapper for d in devices]):
            return devices
        else:
            raise TimePlotGuiException(err_msg)

    def _create_data_item(self, id_nr):
        """returns a data item
        
        Parameter
        ---------
        id_nr : 
            reference number of data item.
            
        """
        data_item = TimePlotDataItem(
            data_fn = self.data_fn, 
            id_nr=id_nr, 
            absolute_time=self.t0
        )
        return data_item

    def _add_data_item(self, id_nr, data_item):
        """add data_item to data_table and to plot item
        
        Parameter
        ---------
        id_nr : int
            number is used as id reference in data_table
        data_item : TimePlotDataItem object
            represents one data line in the plot
            
        """
        self.data_table.update(
            {id_nr: data_item}
        )
        self.graphItem.addItem(data_item.get_plot_data_item())
    
    def _remove_data_item_(self, id_nr):
        timeplotdataitem = self.data_table[id_nr]
        self.graphItem.removeItem(
            self.data_table[id_nr].get_plot_data_item()
        )
        del timeplotdataitem
        self.data_table.pop(id_nr)

    def _remove_data_item(self, id_nr):
        """add data_item to data_table and to plot item
        
        Parameter
        ---------
        id_nr : int
            number is used as id reference in data_table
            
        """
        self.graphItem.removeItem(
            self.data_table[id_nr].get_plot_data_item()
        )
        self.data_table.pop(id_nr)


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
        self.context_menu._add_line_settings_menu()

    def resize_line_settings(self):
        """resizes line settings to make number of data object present
        
        If thread is started the number of data objects corresponds to number 
        of devices concted. If thread does not run, number of data objects
        is given by length of data_table
        
        """
        if self.started:
            self.coerce_same_length(data_length = len(self.dev_lst))
            self.resize_data_table()
        else:
            self.coerce_same_length(data_length = len(self.data_table))
        self.set_line_settings()

    def resize_data_table(self):
        """resizes data table to make number of data object match with devices
        connected
        
        Function adds or removes data_items from data table as long as number 
        of data items does not match to number of devices connceted to 
        TimePlotGui
        
        """
        len_data_table = len(self.data_table)
        while self.dev_num != len_data_table:
            if self.dev_num > len_data_table:
                id_nr = len_data_table
                data_item = self._create_data_item(id_nr)
                self._add_data_item(id_nr, data_item)
            else:
                self._remove_data_item(id_nr)
            len_data_table = len(self.data_table)


    # def coerce_same_length_(self, data_length):
    #     while data_length != len(self.settings['line_settings']):
    #         if data_length > len(self.settings['line_settings']):
    #             self.settings['line_settings'][str(len(self.settings['line_settings']))] = \
    #                         self.plot_item_settings.get_default_line_settings()
    #                         # self.plot_item_settings.default_line_settings
    #         elif data_length < len(self.settings['line_settings']):
    #             self.settings['line_settings'].popitem()

    def coerce_same_length(self, data_length):
        n_lines = self.plot_item_settings.get_nr_lines()
        while data_length != n_lines:
            if data_length > n_lines:
                self.plot_item_settings.add_line()
            else:
                self.plot_item_settings.remove_line()
            n_lines = self.plot_item_settings.get_nr_lines()



    def set_custom_settings(self):
        """updates PlotItem settings with values from settings dictionary
        """

        # Log mode
        self.graphItem.setLogMode(
            x = self.settings['xscalelog'],
            y = self.settings['yscalelog']
        )

        # grid lines
        self.graphItem.showGrid(
            x = self.settings['xgridlines'],
            y = self.settings['ygridlines'],
            alpha = self.settings['gridopacity']
        )

        # line settings
        self.set_line_settings()

        # autopan
        self.viewbox.setAutoPan(x = self.settings['autoPan'])

        # axis limits
        self.viewbox.setRange(
            xRange = self.settings['xlim'],
            yRange = self.settings['ylim']
        )

        # autorange
        self.viewbox.enableAutoRange(
            x = self.settings['xautorange'],
            y = self.settings['yautorange']
        )

        # auto_clear
        self.context_menu.data_options.automatic_clear_checkbox.setChecked(
            self.settings['auto_clear_data']
        )

        # zoom
        self.viewbox.setMouseEnabled(
            x = self.settings['x_zoom'],
            y = self.settings['y_zoom']
        )

        # mouse mode
        if self.settings['mouseMode'] == 1:
            self.viewbox.setLeftButtonAction(mode = 'rect')
        else:
            self.viewbox.setLeftButtonAction(mode = 'pan')

        # frequency state
        self.frequency_state = self.settings['frequency_state']
        self.graphItem.ctrl.fftCheck.setChecked(self.frequency_state)

        # autosave
        self.set_all_autosave(self.settings['do_autosave'])
        self.set_all_autosave_nr(self.settings['autosave_nr'])

        # time stamp
        self.change_time_markers(self.settings['relative_timestamp'])

        # labels
        self.update_plot_labels()

    def set_line_settings(self):
        """updates PlotDataItem settings with values from settings dictionary
        """
        for line_nr, time_data_item in self.data_table.items():
            data_item = time_data_item.get_plot_data_item()
            line_setting = self.settings['line_settings'][str(line_nr)]

            data_item.setAlpha(
                alpha = line_setting['line_alpha'],
                auto = False
            )
            data_item.setPen(
                pg.mkPen(
                    width = line_setting['line_width'],
                    color = line_setting['line_color']
                )
            )
            data_item.setFftMode(self.settings['frequency_state'])

    def update_plot_labels(self):
        if self.frequency_state:
            self.set_frequency_labels()
        else:
            self.set_time_labels()

    def change_label_state(self):
        self.frequency_state = self.graphItem.ctrl.fftCheck.isChecked()
        self.update_plot_labels()

    def set_frequency_labels(self):
        """sets title, xlabel, and ylabel settings in PlotItem object if
        TimePlotGui is in FFT mode

        """
        labels = self.get_axis_labels()
        labels.update({
            'title':    'Fourier Transform of ' + labels['title'],
            'x_label':  'Frequency [Hz]',
            'y_label':  'Amplitude'
        })
        self._set_labels(**labels)

    def set_time_labels(self):
        """sets title, xlabel, and ylabel settings in PlotItem object if
        TimePlotGui is not in FFT mode

        """
        labels = self.get_axis_labels()
        self._set_labels(**labels)


    def _set_labels(self, title, title_font_size, title_font_color, x_label,
                    x_font_size, x_font_color, y_label, y_font_size,
                    y_font_color):
        """sets title, xlabel, and ylabel settings in PlotItem object"""
        self.graphItem.setTitle(
            title,
            color=title_font_color,
            size=title_font_size
        )
        self.graphItem.setLabel(
            'left', y_label,
            **{'color':y_font_color, 'font-size': y_font_size}
        )
        self.graphItem.setLabel(
            'bottom', x_label,
            **{'color': x_font_color, 'font-size': x_font_size}
        )
        return

    def get_axis_labels(self):
        """returns dictionary with formated xlabel, ylabel, and title settings

        Formating of the displayed xlabel, ylabel, and title strings is defined
        in this function. The *axis_data_type* and *axis_unit* stored in the
        settings dictionary are used to construct the x and ylabel strings

        """
        tmp = self.settings['labels'].copy()

        # concatenate label strings
        if tmp['x_axis_unit'] == '':
            x_label = tmp['x_axis_data_type']
        else:
            x_label = '{} [{}]'.format(
                tmp['x_axis_data_type'],
                tmp['x_axis_unit']
            )

        if tmp['y_axis_unit'] == '':
            y_label = tmp['y_axis_data_type']
        else:
            y_label = '{} [{}]'.format(
                tmp['y_axis_data_type'],
                tmp['y_axis_unit']
            )

        labels = {
            'x_label':  x_label,
            'y_label':  y_label,
            'title':    tmp['title_text']
        }

        # reformat font_size values
        labels.update({
            'x_font_size':          str(tmp['x_axis_font_size']) + 'pt',
            'y_font_size':          str(tmp['y_axis_font_size']) + 'pt',
            'title_font_size':      str(tmp['title_font_size']) + 'pt'
        })

        # extract color values
        labels.update({
            'x_font_color':          tmp['x_axis_font_color'],
            'y_font_color':          tmp['y_axis_font_color'],
            'title_font_color':      tmp['title_font_color']
        })

        return labels

    def save_current_settings(self):
        """updates settings dictionary from settings in PloIem and saves then
        to JSON file
        """
        self.save_line_settings()
        viewboxstate = self.viewbox.getState()
        settings = {
          # log mode
            'xscalelog':        self.graphItem.ctrl.logXCheck.isChecked(),
            'yscalelog':        self.graphItem.ctrl.logYCheck.isChecked(),
          # grid lines
            'xgridlines':       self.graphItem.ctrl.xGridCheck.isChecked(),
            'ygridlines':       self.graphItem.ctrl.yGridCheck.isChecked(),
            'gridopacity':      self.graphItem.ctrl.gridAlphaSlider.value()/255,
          # autopan
            'autoPan':          viewboxstate['autoPan'][0],
          # axis limits
            'xlim':             viewboxstate['targetRange'][0],
            'ylim':             viewboxstate['targetRange'][1],
          # autorange
            'xautorange':       viewboxstate['autoRange'][0],
            'yautorange':       viewboxstate['autoRange'][1],
          # auto clear
            'auto_clear_data':  self.context_menu.data_options.automatic_clear_checkbox.isChecked(),
          # zoom
            'x_zoom':           viewboxstate['mouseEnabled'][0],
            'y_zoom':           viewboxstate['mouseEnabled'][1],
          # mouse mode
            'mouseMode':        viewboxstate['mouseMode'],
          # frequency
            'frequency_state':  self.graphItem.ctrl.fftCheck.isChecked(),
          # autosave
            'do_autosave':      self.context_menu.data_options.autosave.defaultWidget().layout().itemAt(0).widget().isChecked(),
            'autosave_nr':      self.context_menu.data_options.autosave.defaultWidget().layout().itemAt(1).widget().value(),
          # time stamp

          # labels
            'labels':           self.settings['labels'],
          # auto visible only
            'autoVisibleOnly_x': self.context_menu.autoVisibleOnly_x.isChecked(),
            'autoVisibleOnly_y': self.context_menu.autoVisibleOnly_y.isChecked(),
        # alpha
            'plotalpha':        self.graphItem.alphaState(),

        }
        self.plot_item_settings.save_settings(**settings)

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
        self.plot_item_settings = PlotItemSettings(number_of_lines=self.dev_num)
        self.settings = self.plot_item_settings.get_default_settings()
        self.settings['line_settings'] = temp_line_settings
        self.resize_line_settings()
        # ===============================
        # Implement the settings
        # ===============================
        self.context_menu.ammend_context_menu()
        self.set_custom_settings()

    def clear_line_settings(self):
        # self.settings['line_settings'] = self.plot_item_settings.DEFAULT_SETTINGS['line_settings']
        self.clear_all_line_settings()
        self.set_line_settings()
        self.context_menu.ammend_context_menu()


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
        data_fname, file_info = QFileDialog.getOpenFileName(
            self,
            'Select data file',
            '~/',
            "JSON files (*.json)"
        )
        if data_fname != '':
            settings_fname, file_info = QFileDialog.getOpenFileName(
                self,
                'Select settings file',
                '~/',
                "JSON files (*.json)"
            )
            if settings_fname !='':
                del self.plot_item_settings
                self.plot_item_settings = PlotItemSettings(
                    unusal_settings_file = settings_fname
                )
                self.settings = self.plot_item_settings.settings
            if data_fname is not None:
                self.clear_all_plot_data_items()
                self._init_data_table(self.dev_lst, new_data = data_fname)
                self.resize_line_settings()
                self.context_menu._add_line_settings_menu(self.data_table)
                self.set_custom_settings()
                # self.ammend_context_menu()

    def set_local_ft_mode(self, local_ft_mode):
        """starts or stops the local FT mode depending on local fourier checkbox
        state
        """
        if local_ft_mode:
            if not self.graphItem.ctrl.fftCheck.isChecked():
                for dataitem in self.data_table.values():
                    dataitem.start_local_ft_mode()
                    # print('%%%%%% started local fourier mode')
            else:
                self.transform_menu.local_fourier.defaultWidget().layout().itemAt(1).widget().setChecked(False)
                self.local_ft_error()
        else:
            for dataitem in self.data_table.values():
                dataitem.stop_local_ft_mode()
                # print('%%%%%% stopped local fourier mode')
        return

    def clear_all_plot_data_items(self):
        data_items = self.graphItem.listDataItems()
        for data_item in data_items:
            self.graphItem.removeItem(data_item)

    def save_data_settings(self):
        self.plot_item_settings.save_settings(
            auto_clear_data = self.context_menu.data_options.automatic_clear_checkbox.isChecked()
        )

    def save_line_settings(self):
        line_controls = self.context_menu.line_settings_menu.actions()[0::2]
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
        """store all data objects

        Function stores data of every data_item by calling its store_data().
        To avoid problems when importing data the next time this function
        temporarily disables FFT, x log, and y log mode.

        """

        # save current state
        frequency_state = self.frequency_state
        x_log_check = self.context_menu.x_log_check.isChecked()
        y_log_check = self.context_menu.y_log_check.isChecked()

        # disable FFT, x log, and y log mode
        self.graphItem.ctrl.fftCheck.setChecked(False)
        self.context_menu.x_log_check.setChecked(False)
        self.context_menu.y_log_check.setChecked(False)

        # sava data
        if path.exists(self.data_fn):
            os.remove(self.data_fn)
        for data_item in self.data_table.values():
            data_item.store_data()

        # restore FFT,x log, and y log states
        self.graphItem.ctrl.fftCheck.setChecked(frequency_state)
        self.context_menu.x_log_check.setChecked(x_log_check)
        self.context_menu.y_log_check.setChecked(y_log_check)

    def change_time_markers(self, relative_time):
        self.axis_item.relative_time = relative_time

    def set_all_autosave(self, autosave):
        for data_item in self.data_table.values():
            data_item.do_autosave = autosave

    def set_all_autosave_nr(self, autosave_nr):
        for data_item in self.data_table.values():
            data_item.autosave_nr = autosave_nr


    def clear_all_data(self):
        """clears data in all data items bby calling the corresponding clear()
        function

        """
        self.reset_absolute_time_stamp()
        for data_item in self.data_table.values():
            data_item.clear_data()
            data_item.reset_absolute_time(absolute_time=self.t0)

    def change_title(self):
        title, acccepted = QInputDialog.getText(
            self,
            'Change title',
            'Enter new title:'
        )
        if acccepted:
            self.settings['labels']['title_text'] = title
            self.update_plot_labels()

    def change_x_axis_label(self):
        axis_label, acccepted = QInputDialog.getText(
            self,
            'Change x axis label',
            'Enter new label:'
        )
        if acccepted:
            self.settings['labels']['x_axis_data_type'] = axis_label
            self.update_plot_labels()

    def change_y_axis_label(self):
        axis_label, acccepted = QInputDialog.getText(
            self,
            'Change y axis label',
            'Enter new label:'
        )
        if acccepted:
            self.settings['labels']['y_axis_data_type'] = axis_label
            self.update_plot_labels()

    def _set_central_wid_properties(self):
        """ """
        self.central_wid.setAutoFillBackground(True)
        p = self.central_wid.palette()
        p.setColor(self.central_wid.backgroundRole(), QtCore.Qt.darkGray)
        self.central_wid.setPalette(p)


    def _init_multi_worker_thread(self, devices):
        """initializes a worker thread for every devicewrapper in devices"""

        # set up QWaitCondition
        self.mutex_table = {
            idx: QMutex() for idx in range(len(devices))
        }
        self.cond_table = {
            idx: QWaitCondition() for idx in range(len(devices))
        }

        # set up the measurement engine
        self.worker_table = {}
        for idx, devicewrapper in enumerate(devices):
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

        msg = """
        You are exiting FFT Transform mode and entering Time Dependence
        mode. If you would like to re-enter FFT Transform mode, you may
        do so from the context menu.
        """
        mode_change_popup = QMessageBox()
        mode_change_popup.setText(msg)
        mode_change_popup.setIcon(QMessageBox.Information)
        mode_change_popup.exec_()

    def local_ft_error(self):

        msg = """
        You are already in FFT mode. If you would like a local transform,
        please select a region in Time Dependence mode.
        """
        local_ft_error = QMessageBox()
        local_ft_error.setText(msg)
        local_ft_error.setIcon(QMessageBox.Information)
        local_ft_error.exec_()

    def y_autopan_warning(self):

        msg = """
        Auopanning functionality for the y axis is not supported.
        """
        y_autopan_warning = QMessageBox()
        y_autopan_warning.setText(msg)
        y_autopan_warning.setIcon(QMessageBox.Information)
        y_autopan_warning.exec_()



    def start_thread(self):
        """start data acquisition in worker thread

        if clauses handle the following causes: previous data are removed if
        autoclear button is checked. FFT mode is switched off and warning
        QMessage is emitted if previous data is removed.


        """
        if self.start_button_counter == 0:
            self.start_button_counter += 1
            is_checked = False
            if self.context_menu.data_options.automatic_clear_checkbox.isChecked():
                if self.graphItem.ctrl.fftCheck.isChecked():
                    is_checked = True
                self.graphItem.ctrl.fftCheck.setChecked(False)
                self.clear_all_data()
            self.start_signal.emit()
            if is_checked:
                self.leaving_fft_mode()
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
        """updates TimePlotDataItem object with corresponding id_nr"""

        # save current state
        frequency_state = self.frequency_state
        x_log_check = self.context_menu.x_log_check.isChecked()
        y_log_check = self.context_menu.y_log_check.isChecked()

        # disable FFT, x log, and y log state
        self.graphItem.ctrl.fftCheck.setChecked(False)
        self.context_menu.x_log_check.setChecked(False)
        self.context_menu.y_log_check.setChecked(False)

        # update value
        self.data_table[id_nr].append_value(val, time_val)

        # reinstate FFT, x log, and y log state
        self.graphItem.ctrl.fftCheck.setChecked(frequency_state)
        self.context_menu.x_log_check.setChecked(x_log_check)
        self.context_menu.y_log_check.setChecked(y_log_check)


    @QtCore.pyqtSlot(int, float, float)
    def newReading(self, id_nr, val, time_val):
        """ """
        pg.QtGui.QApplication.processEvents()
        self.update_datapoint(id_nr, val, time_val)
        time.sleep(self.sampling_latency)
        # necessary to avoid worker to freeze
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
# MainWindow
# ===========================================================================
class TimePlotMainWindow(QMainWindow):
    """ """
    # xpos on screen, ypos on screen, width, height
    DEFAULT_GEOMETRY = [400, 400, 1000, 500]

    def __init__(self, devices=None):
        super(TimePlotMainWindow, self).__init__()
        self._init_ui(devices=devices)

    def _init_ui(self, window_geometry=None, devices=None):
        self.setGeometry()
        self.setWindowTitle('time-plot')
        self.setStyleSheet("background-color: black;")
        self.time_plot_ui = TimePlotGui(
            parent=None,
            window=self,
            devices=devices,
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
            args = TimePlotMainWindow.DEFAULT_GEOMETRY
        super(TimePlotMainWindow, self).setGeometry(*args, **kwargs)

    def closeEvent(self, event):
        """ """
        print('event')
        self.time_plot_ui.closeEvent(event)
#        event.accept

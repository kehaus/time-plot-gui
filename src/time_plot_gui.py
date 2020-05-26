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
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QMainWindow
from PyQt5.QtWidgets import qApp, QAction, QMenu, QGridLayout, QLabel, QLineEdit, QSizePolicy
from PyQt5.QtGui import QIcon, QFont, QCursor, QRegion, QPolygon
from PyQt5 import QtCore, Qt, QtGui
import pyqtgraph as pg


from time_plot_worker import TimePlotWorker
from plot_item_settings import PlotItemSettings, DataRecall, JSONFileHandler

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

        self.create_absolute_time_stamp()
        self.data_fn = TimePlotGui.DEFAULT_DATA_FILENAME

        if type(devicewrapper_lst) == DeviceWrapper:
            devicewrapper_lst = [devicewrapper_lst]

        self.plot_item_settings = PlotItemSettings()

# <<<<<<< HEAD

# =======
        # self.absolute_time = []
        # self.time_array = []
        # self.potential = []
        # self.data_recall = DataRecall()
        # if path.exists(self.data_recall.STORED_DATA_FILENAME):
        #     self.set_data()
        # else:
        #     self.time_array = np.array([])
        #     self.potential = np.array([])
        #     self.absolute_time = np.array([])
        # self.data = np.array([])
# >>>>>>> time_plot_gui_development

        self._init_ui(window, devicewrapper_lst)
        self._init_multi_worker_thread(devicewrapper_lst)


    def _init_ui(self, mainwindow, devicewrapper_lst):

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

        # =====================================================================
        # control buttons - layout
        # =====================================================================
        # self.startBtn = QPushButton('START')
        # self.controls_layout.addWidget(self.startBtn, 0, 0, 1, 1)
        # self.startBtn.setStyleSheet("background-color: white;")
        #
        # self.stopBtn = QPushButton('STOP')
        # self.controls_layout.addWidget(self.stopBtn, 1, 0, 1, 1)
        # self.stopBtn.setStyleSheet("background-color: white;")
        #
        # self.controls_layout.addWidget(self.vl, 0, 1, 1, 1)
        # #self.comboBox = QComboBox(self)
        # #comboBox.addItem()
        # #self.controls_layout.addWidget(self.comboBox, 0, 1, 1, 1)

        self.playBtn = QPushButton()
        self.playBtn.setFixedSize(QSize(30, 30))
        self.playBtn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        points = [QPoint(0, 0), QPoint(0, self.playBtn.height()), QPoint(self.playBtn.width(), self.playBtn.height()/2)]
        self.playBtn.setMask(QRegion(QPolygon(points)))
        #self.graphics_layout.addWidget(self.playBtn, 0, 0)
        self.playBtn.setStyleSheet("background-color: rgb(120,120,120);")

        self.squarestopBtn = QPushButton()
        self.squarestopBtn.setFixedSize(QSize(110, 30))
        self.squarestopBtn.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        points = [QPoint((self.squarestopBtn.width()+50)/2, 0), \
                QPoint((self.squarestopBtn.width()+50)/2, self.squarestopBtn.height()), \
                QPoint(self.squarestopBtn.width(), self.squarestopBtn.height()), \
                QPoint(self.squarestopBtn.width(), 0)]
        self.squarestopBtn.setMask(QRegion(QPolygon(points)))
    #    self.graphics_layout.addWidget(self.squarestopBtn, 0, 1)
        self.squarestopBtn.setStyleSheet("background-color: rgb(120,120,120);")

        self.blankWidget = QWidget()
        self.blankWidget.setFixedSize(QSize(500, 30))
        self.graphics_layout.addWidget(self.blankWidget, 0, 2)

        self.blankWidget2 = QWidget()
        self.blankWidget2.setFixedSize(QSize(30, 30))
        self.graphics_layout.addWidget(self.blankWidget2, 0, 1)


        self.init_plot(devicewrapper_lst)
        self.graphics_layout.addWidget(self.squarestopBtn, 0, 0)
        self.graphics_layout.addWidget(self.playBtn, 0, 0)
        self.graphics_layout.addWidget(self.blankWidget2, 0, 1)

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
        # self.startBtn.clicked.connect(self.start_thread)
        # self.stopBtn.clicked.connect(self.stop_thread)

        self.playBtn.clicked.connect(self.start_thread)
        self.squarestopBtn.clicked.connect(self.stop_thread)

       # ============================================================
        # put everything together
        # ============================================================
        self.wid_layout.addItem(self.graphics_layout, 0, 0, 6, 6)
        #self.wid_layout.addItem(self.controls_layout, 0, 0, 2, 2)
        # self.wid_layout.setColumnStretch(0, 10)
        # self.wid_layout.setColumnStretch(8, 2)

        self.central_wid.setLayout(self.wid_layout)

    def init_plot(self, devicewrapper_lst):
        """ """
        print("initializing plot...")
        # if len(self.potential) != 0:
        #     self.graphWidget.removeItem(self.graphItem)
        #     self.graphics_layout.removeWidget(self.graphWidget)
        self.graphWidget = pg.PlotWidget()
        self.graphItem = self.graphWidget.getPlotItem()
        self.viewbox = self.graphItem.getViewBox()
        self.modify_context_menu()
        self.graphics_layout.addWidget(self.graphWidget, 0, 0, 5, 4)
        #self.graphics_layout.addWidget(self.blankWidget2, 2, 2)
        self.graphItem.setTitle('Potential over Time', **{'color': '#FFF', 'size': '20pt'})
        #self.graphWidget.showAxis('top', False)
        self.graphItem.setLabel('left', 'Potential (Volts)', color='white', size=30)
        self.graphItem.setLabel('bottom', 'Time (seconds)', color='white', size=30)

        # ===============================
        # initlialize data lines
        # ===============================
        self.init_data_items(devicewrapper_lst)
        self.align_time_stamps()

        # ===============================
        # customize plot settings with stored values
        # ===============================
        self.set_custom_settings()


    def init_data_items(self, devicewrapper_lst):
        self.data_table = {}
        for id_nr, dw in enumerate(devicewrapper_lst):
            data_item = TimePlotDataItem(id_nr=id_nr, absolute_time=self.t0)
            self.data_table.update(
                {id_nr: data_item}
            )
            if not self.data_options.automatic_clear_checkbox.isChecked():
                data_item.recall_data(self.data_fn)
            self.graphItem.addItem(data_item.get_plot_data_item())


    def create_absolute_time_stamp(self):
        self.t0 = time.time()

    def reset_absolute_time_stamp(self):
        self.t0 = time.time()

    def align_time_stamps(self):
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


    def set_custom_settings(self):
        # acquires the self.settings varibale from plot_item_settings
        if path.exists(self.plot_item_settings.SETTINGS_FILENAME):
            self.settings = self.plot_item_settings.settings
        else:
            self.settings = self.plot_item_settings.DEFAULT_SETTINGS

        self.graphItem.setLogMode(x = self.settings['xscalelog'], y = self.settings['yscalelog'])
        self.graphItem.showGrid(x = self.settings['xgridlines'], y = self.settings['ygridlines'], \
                                alpha = self.settings['gridopacity'])
        #self.plotDataItem.setAlpha(alpha = self.settings['plotalpha'][0], auto = self.settings['plotalpha'][1])
        self.viewbox.setAutoPan(x = self.settings['autoPan'])
        self.viewbox.setRange(xRange = self.settings['xlim'], yRange = self.settings['ylim'])
        self.viewbox.enableAutoRange(x = self.settings['xautorange'], y = self.settings['yautorange'])
        self.data_options.automatic_clear_checkbox.setChecked(self.settings['auto_clear_data'])
        self.viewbox.setMouseEnabled(x = self.settings['x_zoom'], y = self.settings['y_zoom'])

    def save_current_settings(self):
        #self.plot_item_settings = PlotItemSettings()
        viewboxstate = self.viewbox.getState()
        #print(f"{viewboxstate}")
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
            x_zoom = viewboxstate['mouseEnabled'][0],
            y_zoom = viewboxstate['mouseEnabled'][0],
            auto_clear_data = self.data_options.automatic_clear_checkbox.isChecked()
        )
        self.plot_item_settings.save(self.plot_item_settings.settings_filename, self.plot_item_settings.settings)
        self.set_custom_settings()

    # rename as "restore_default_settings"
    def default_settings(self):
        #self.plot_item_settings = PlotItemSettings()
        if path.exists(self.plot_item_settings.settings_filename):
            os.remove(self.plot_item_settings.settings_filename)
        self.set_custom_settings()

    def modify_context_menu(self):
        self.menu = self.graphItem.getMenu()

        self.visualization_settings = self.menu.addMenu("Visualization Settings")

        restore_default = QtGui.QAction("Restore Default Plot Settings", self.visualization_settings)
        restore_default.triggered.connect(self.default_settings)
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

        self.data_options = self.menu.addMenu("Data Options")

        clear_data = QtGui.QAction("Clear Data", self.data_options)
#        clear_data.triggered.connect(self.clear_current_data)
        clear_data.triggered.connect(self.clear_all_data)
        self.data_options.addAction(clear_data)
        self.data_options.clear_data = clear_data

        automatic_clear = QtGui.QWidgetAction(self.data_options)
        automatic_clear_checkbox = QtGui.QCheckBox("Automatically Clear Data", self)
        automatic_clear.setDefaultWidget(automatic_clear_checkbox)
        self.data_options.addAction(automatic_clear)
        self.data_options.automatic_clear = automatic_clear
        self.data_options.automatic_clear_checkbox = automatic_clear_checkbox

        # self.zoom_settings = self.menu.addMenu("Zoom Settings")
        #
        # x_zoom = QtGui.QWidgetAction(self.zoom_settings)
        # x_zoom_checkbox = QtGui.QCheckBox()
        # x_zoom.setDefaultWidget(x_zoom_checkbox)
        # x_zoom_checkbox.stateChanged.connect(self.update_zoom_settings)
        # self.zoom_settings.addAction(x_zoom)
        # self.zoom_settings.x_zoom = x_zoom
        # self.zoom_settings.x_zoom_checkbox = x_zoom_checkbox
        #
        # y_zoom = QtGui.QWidgetAction(self.zoom_settings)
        # y_zoom_checkbox = QtGui.QCheckBox()
        # y_zoom.setDefaultWidget(y_zoom_checkbox)
        # self.zoom_settings.addAction(y_zoom)
        # self.zoom_settings.y_zoom = y_zoom
        # self.zoom_settings.y_zoom_checkbox = y_zoom_checkbox

    def store_all_data(self):
        """
        **inehrits store_current_data function to adjust for multi-line-plotting**

        """
        for data_item in self.data_table.values():
            data_item.store_data(fn=self.data_fn)

    def clear_all_data(self):
        """
        **inherits clear_current_data function to adjust for multi-line-plotting**
        """
        self.reset_absolute_time_stamp()
        for data_item in self.data_table.values():
            data_item.clear_data()
            data_item.reset_absolute_time(absolute_time=self.t0)


    def store_current_data(self, time_axis, absolute_time, y):
        """
        **obsolete**
        """
        time_data = time_axis.tolist()
        absolute_time_data = absolute_time.tolist()
        y_data = y.tolist()
        # for argument in **kwargs:
        #     argument.tolist()
        self.data_recall.store(time_data, absolute_time_data, y_data)

    def clear_current_data(self):
        """
        **obsolete**
        """
        self.time_array = np.array([])
        self.potential = np.array([])
        self.absolute_time = np.array([])
        self.data_recall.clear_data()
        self.plotDataItem.setData(self.time_array, self.potential)
        self.set_data()

    # def set_data(self):
    #     self.time_array, self.absolute_time, self.potential = self.data_recall.load_data()

    def update_zoom_settings(self):
        x_zoom = self.zoom_settings.x_zoom_checkbox.isChecked()
        y_zoom = self.zoom_settings.y_zoom_checkbox.isChecked()
        self.viewbox.setMouseEnabled(x = self.settings['x_zoom'], y = self.settings['y_zoom'])


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
        # self.time_array = np.array([])
        # self.potential = np.array([])
        if self.data_options.automatic_clear_checkbox.isChecked():
#            self.clear_current_data()
            self.clear_all_data()
        self.start_signal.emit()

    def stop_thread(self):
        self.stop_signal.emit()

    def update_datapoint(self, id_nr, val):
        """updates TimePlotDataItem object with corresponding to id_nr"""
        self.data_table[id_nr].add_value(val)

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
#            self.store_current_data(self.time_array, self.absolute_time, self.potential)
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
        ## Perform fourier transform. If x values are not sampled uniformly,
        ## then use np.interp to resample before taking fft.
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
    window.show()
    app.exec_()


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

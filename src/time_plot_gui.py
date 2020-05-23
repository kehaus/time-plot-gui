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

    def __init__(self, parent=None, window=None, devicewrapper_lst=None):
        """ """
        super(TimePlotGui, self).__init__(parent=parent)
        # self.absolute_time = []
        # self.time_array = []
        # self.potential = []
        # self.absolute_time = np.array([])
        # self.time_array = np.array([])
        # self.potential = np.array([])
        # self.data = np.array([])
        
        if type(devicewrapper_lst) == DeviceWrapper:
            devicewrapper_lst = [devicewrapper_lst]
        
        # devicewrapper_lst = [devicewrapper]
        
        self._init_ui(window, devicewrapper_lst)
        
        # self._init_worker_thread(devicewrapper)
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
        self.vl = pg.ValueLabel(formatStr='{avgValue:0.2f} {suffix}')
        self.vl.setStyleSheet("color: white;")
        
        self.vl.setValue(-1)
        # if len(self.potential) == 0:
        #     self.vl.setValue(-1)
        # else:
        #     self.vl.setValue(self.potential[-1])
            
        self.vl.setFixedSize(QSize(40, 30))
        #self.graphics_layout.addWidget(self.vl, 0, 3)

        # =====================================================================
        # control panel
        # =====================================================================
        #self.controls_layout = QGridLayout()


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
        self.graphics_layout.addWidget(self.vl, 0, 3)

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
        
        self.data_table = {}
        self.t0 = time.time()
        for id_nr, dw in enumerate(devicewrapper_lst):
            data_item = TimePlotDataItem(absolute_time=self.t0)
            self.data_table.update(
                {id_nr: data_item}
            )
            self.graphItem.addItem(data_item.get_plot_data_item())
            print('   ***was here***')
        
        # self.data_item = TimePlotDataItem(absolute_time=self.t0)
        # self.data_table.update({0:self.data_item})
        # self.graphItem.addItem(self.data_table[0].get_plot_data_item())
        
        
        self.set_custom_settings()

    def set_custom_settings(self):
        self.plot_item_settings = PlotItemSettings()
        # acquires the self.settings varibale from plot_item_settings
        if path.exists(self.plot_item_settings.SETTINGS_FILENAME):
            settings = self.plot_item_settings.settings
        else:
            settings = self.plot_item_settings.DEFAULT_SETTINGS
        self.graphItem.setLogMode(x = settings['xscalelog'], y = settings['yscalelog'])
        self.graphItem.showGrid(x = settings['xgridlines'], y = settings['ygridlines'], \
                                alpha = settings['gridopacity'])
        # self.plotDataItem.setAlpha(alpha = settings['plotalpha'][0], auto = settings['plotalpha'][1])
        self.viewbox.setAutoPan(x = settings['autoPan'])
        self.viewbox.setRange(xRange = settings['xlim'], yRange = settings['ylim'])
        self.viewbox.enableAutoRange(x = settings['xautorange'], y = settings['yautorange'])

    def save_current_settings(self):
        self.plot_item_settings = PlotItemSettings()
        viewboxstate = self.viewbox.getState()
        self.plot_item_settings.save(autoPan = viewboxstate['autoPan'][0],
                                    xscalelog = self.graphItem.ctrl.logXCheck.isChecked(),
                                    yscalelog = self.graphItem.ctrl.logYCheck.isChecked(),
                                    xlim = viewboxstate['targetRange'][0],
                                    ylim = viewboxstate['targetRange'][1],
                                    xautorange = viewboxstate['autoRange'][0],
                                    yautorange = viewboxstate['autoRange'][1],
                                    xgridlines = self.graphItem.ctrl.xGridCheck.isChecked(),
                                    ygridlines = self.graphItem.ctrl.yGridCheck.isChecked(),
                                    gridopacity = self.graphItem.ctrl.gridAlphaSlider.value()/255,
                                    plotalpha = self.graphItem.alphaState()
                                    )
        self.set_custom_settings()

    # rename as "restore_default_settings"
    def default_settings(self):
        self.plot_item_settings = PlotItemSettings()
        if path.exists(self.plot_item_settings.settings_filename):
            os.remove(self.plot_item_settings.settings_filename)
        self.set_custom_settings()

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


    def _set_central_wid_properties(self):
        """ """
        self.central_wid.setAutoFillBackground(True)
        p = self.central_wid.palette()
        p.setColor(self.central_wid.backgroundRole(), QtCore.Qt.darkGray)
        self.central_wid.setPalette(p)


    def _init_multi_worker_thread(self, devicewrapper_lst):
        """ 
        
        * create plotData_lst
        * update_ValueLabel
        """

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
        

#     def _init_worker_thread(self, devicewrapper):
#         """ """

#         # Setup QWaitCondition
#         self.mutex = QMutex()
#         self.cond = QWaitCondition()

#         # Setup the measurement engine
# #        self.mthread = QtCore.QThread()
#         self.worker = TimePlotWorker(devicewrapper, self.mutex, self.cond)


#         # connect signal and slots
#         self.start_signal.connect(self.worker.start)
#         self.stop_signal.connect(self.worker.stop)


#         self.worker.reading.connect(self.newReading)
#         return


    def start_thread(self):
        self.start_signal.emit()

    def stop_thread(self):
        self.stop_signal.emit()


#     def update_ValueLabel(self, id_nr, val):
#         """ """
# #        self.vl.setValue(val)

#         self.update_time_array(val)
#         potential_axis = self.potential
#         time_axis = self.time_array
#         data = self.data
#         self.plotDataItem_lst[id_nr].setData(time_axis, potential_axis)
        


    # def update_time_array(self, val):
    #     """ """
    #     #self.potential.append(val)
    #     self.potential = np.append(self.potential, np.array([val]))
    #     self.absolute_time = np.append(self.absolute_time, np.array([time.time()]))
    #     self.time_array = np.array([x - self.absolute_time[0] for x in self.absolute_time])
    #     self.data = np.append(self.data, np.array([(self.potential[-1], self.time_array[-1])]))

    def update_datapoint(self, id_nr, val):
        """ """
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
            event.accept()
        else:
            event.ignore()


# ===========================================================================
# helper class - Data item
# ===========================================================================
class TimePlotDataItem(object):
    """wraps the pq.PlotCurveItem class to extend functionality
    
    Main functionality enhancement is that PlotCurveItem data can now be 
    extended by providing a single value. Internal functionality will take care
    of generating corresponding time valu and appending the the Data object of
    PlotCurveItem
    
    TO INCLUDE:
        * automatic saving mechanism
    
    """
    
    def __init__(self, absolute_time=None):
        self.pdi = pg.PlotDataItem([],[])
        if absolute_time == None:
            self.absolute_time = time.time()
        else:
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
        """returns the pg.PlotDataItem time and data arrrays"""
        return self.pdi.getData()


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
    dd3.frequency = 1.2
    dd3.signal_form = 'sin'
    dw3 = DeviceWrapper(dd3)

    dd4 = DummyDevice()
    dd4.frequency = 1.4
    dd4.signal_form = 'sin'
    dw4 = DeviceWrapper(dd4)
    
    dd5 = DummyDevice()
    dd5.frequency = 1.5
    dd5.signal_form = 'sin'
    dw5 = DeviceWrapper(dd5)
    
    main([dw1,dw3,dw4,dw5])

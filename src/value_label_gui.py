#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ValueLabelGui class creates a GUI displaying the time trace of a value from a 
given device object




"""

__version__ = "0.0.1"
__author__ = "kha"



import os
import ctypes as ct
import numpy as np
import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
from unittest.mock import MagicMock


import sys
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QMainWindow
from PyQt5.QtWidgets import qApp, QAction, QMenu, QGridLayout, QLabel
from PyQt5.QtGui import QIcon, QFont, QCursor
from PyQt5 import QtCore
import pyqtgraph as pg


from time_plot_worker import TimePlotWorker

from util.workerthread import WorkerThread,WorkerTaskBase
from util.devicewrapper import DeviceWrapper, DummyDevice


# ============================================================================
# Excpetion class
# ============================================================================
class ValueLabelGuiException(Exception):
    """ """
    pass

# ============================================================================
# ValueLabel class
# ============================================================================

class ValueLabelGui(QWidget):
    
    start_signal = QtCore.pyqtSignal()
    stop_signal = QtCore.pyqtSignal()
    
    def __init__(self, parent=None, window=None, devicewrapper=None):
        """ """
        super(ValueLabelGui, self).__init__(parent=parent)
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
        self.vl.setValue(-1)
        self.graphics_layout.addWidget(self.vl, 0, 0, 4, 4)
        
        
        # =====================================================================
        # control panel
        # =====================================================================
        self.controls_layout = QGridLayout()


        # =====================================================================
        # control buttons - layout
        # =====================================================================
        self.startBtn = QPushButton('START')
        self.controls_layout.addWidget(self.startBtn, 0, 0, 1, 1)
        self.stopBtn = QPushButton('STOP')
        self.controls_layout.addWidget(self.stopBtn, 1, 0, 1, 1)
        
        
        # =====================================================================
        # control buttons - connections
        # =====================================================================
        self.startBtn.clicked.connect(self.start_thread)
        self.stopBtn.clicked.connect(self.stop_thread)

       # ============================================================
        # put everything together
        # ============================================================
        self.wid_layout.addItem(self.graphics_layout, 0, 0, 2, 2)
        self.wid_layout.addItem(self.controls_layout, 0, 2, 2, 2)     
        # self.wid_layout.setColumnStretch(0, 10)
        # self.wid_layout.setColumnStretch(8, 2)
        
        self.central_wid.setLayout(self.wid_layout)


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
            event.accept()
        else:
            event.ignore()  




# ===========================================================================
# 
# ===========================================================================

class MainWindow(QMainWindow):
    """ """
    
    DEFAULT_GEOMETRY = [400, 400, 200, 50]
    
    def __init__(self, devicewrapper=None):
        super(MainWindow, self).__init__()
        self._init_ui(devicewrapper=devicewrapper)
        
    def _init_ui(self, window_geometry=None, devicewrapper=None):
        self.setGeometry()
        self.setWindowTitle('time-plot')
        self.time_plot_ui = ValueLabelGui(
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
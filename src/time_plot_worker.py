#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Worker class for GUI classes

This class extends the workerthread and Devicewrapper classes to allow
continuous data updates in the GUI classes (e.g. TimePlotGui)



"""

__version__ = "0.0.1"
__author__ = "kha"


import time

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from util.workerthread import WorkerThread,WorkerTaskBase
from util.devicewrapper import DeviceWrapper, DummyDevice




# =============================================================================
# Worker Thread
# =============================================================================

class TimePlotWorker(QObject):       # change class name to MeasurementEngine ?
    """ """

    reading = pyqtSignal(int, float, float)
    finished = pyqtSignal()
    started = pyqtSignal()
    killed = pyqtSignal()

    def __init__(self, devicewrapper , mutex, cond, *args, id_nr=0, **kwargs):
        """ """
        QObject.__init__(self)
        print('worker initialized')
        self.dw = devicewrapper
        self.wt = self.dw.wt
        self.dd = self.dw.d
        self.id_nr = id_nr

        self.mtx = mutex
        self.cond = cond
        self._init_workertask()



    def _init_workertask(self):
        wtask = WorkerTaskBase(
            func=self.dd.get_value,
            continuous=True,
            callback=self.read_value
        )
        self.wt.put(wtask)


    def read_value(self, val, verbose=True):
        if verbose:
            print('read val: {:.2f}'.format(val))

        self.mtx.lock()                 # lock worker-thread
        time_val = time.time()
        arg = []
        arg.append(val)
        arg.append(time_val)
        self.reading.emit(self.id_nr, val, time_val)          # emit signalt to update gui
        self.cond.wait(self.mtx)        # wait until gui is updated
        self.mtx.unlock()               # unlock worker thread


    @pyqtSlot()
    def start(self):
        """ """
        print('start worker')
        self.wt.start()

        # inform mainWindow
#        self.started.emit()
        return

    @pyqtSlot()
    def stop(self):
        self.wt.stop()
        print('stopped worker')

        # inform mainWindow
#        self.killed.emit()
        return

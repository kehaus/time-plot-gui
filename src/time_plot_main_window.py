#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import sys

from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWidgets import QWidget, QGridLayout

try:
    from .time_plot_gui import TimePlotGui
except:
    from time_plot_gui import TimePlotGui


# ===========================================================================
# MainWindow class
# ===========================================================================
class TimePlotMainWindow(QMainWindow):
    """ """
    # xpos on screen, ypos on screen, width, height
    DEFAULT_GEOMETRY = [400, 400, 1000, 500]

    def __init__(self, devices=None, **kwargs):
        super(TimePlotMainWindow, self).__init__()
        self._init_ui(devices=devices, **kwargs)

    def _init_ui(self, window_geometry=None, devices=None, **kwargs):
        self.setGeometry()
        self.setWindowTitle('time-plot')
        self.setStyleSheet("background-color: black;")
        self.time_plot_ui = TimePlotGui(
            parent=None,
            window=self,
            devices=devices,
            folder_filename = None,
            **kwargs
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


# ===========================================================================
# GUI start-up function
# ===========================================================================
def start_application(devices, MainWindowClass=None, **kwargs):
    """starts instance of given MainWindowClass as QApplication with devices 
    connected to it.
    
    This function handles the QApplication start up of the gui. This procedure
    and event handling is indepentent of the given MainWindowClass. It can also 
    be used for other MainWindowClasses than the TimePlotMainWindow
    
    
    Parameter
    ---------
    devices : DeviceWrapper object, list
        represents the hardware. 
    MainWindowClass : QMainWindow object
        From this class an instance is created to generate the main window. If
        None is passed a TimePlotMainWindow object is generated.
    kwargs 
        kwargs are passed to in the initialization of the MainWindowClass 
        object
    
    Return
    ------
        returns the inistialized MainWindow object
    
    
    """
    if MainWindowClass is None:
        MainWindowClass = TimePlotMainWindow
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print('QApplication instance already exists {}'.format(str(app)))
    window = MainWindowClass(
        devices=devices, **kwargs
    )
    try:
        window.show()
        app.exec_()
    except:
        window.closeEvent()
    return window
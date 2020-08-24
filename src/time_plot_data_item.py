#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimePlotDataItem wrps the pq.PlotDataItem class to extend functionality.


"""
__version__ = "1.0.0"



from os import path
import time

import numpy as np
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog
import pyqtgraph as pg


try:
    from .plot_item_settings import PlotItemSettings, JSONFileHandler
except:
    from plot_item_settings import PlotItemSettings, JSONFileHandler



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

    def __init__(self, data_fn, id_nr=0, absolute_time=None, do_autosave=True,
                autosave_nr=30):
        self.id_nr = id_nr
        self.data_name = self._compose_data_name()
        self.fn = data_fn
        self.do_autosave = do_autosave
        self.autosave_nr = autosave_nr
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

    def append_value(self, val, time_val):
        """adds value to pg.PlotDataItem data array"""
        t, y = self.pdi.getData()
        t = np.append(t, time_val - self.absolute_time)
        y = np.append(y, val)
        self.pdi.setData(t,y)
        if self.do_autosave:
            if len(t)%self.autosave_nr == 0:
                self.store_data()

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

    def store_data(self, fn=None):
        """saves data as nested dictionary in json file"""

        if fn is None:
            fn = self.fn
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

    def open_color_dialog(self):
        self.restorable_color = self.pdi.opts['pen'].color()
        self.color_dialog = QColorDialog()
        self.color_dialog.currentColorChanged.connect(self.set_color)
        self.color_dialog.rejected.connect(self.cancel_color_dialog)
        self.color_dialog.open()

    def set_color(self):
        self.pdi.update_color(self.color_dialog)

    def cancel_color_dialog(self):
        self.pdi.update_color(self.restorable_color)


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

    def setLogMode(self, xMode, yMode):
        print('setting log mode')
        if self.opts['logMode'] == [xMode, yMode]:
            return
        self.opts['logMode'] = [xMode, yMode]
        self.xDisp = self.yDisp = None
        self.xClean = self.yClean = None
        self.updateItems()
        self.informViewBoundsChanged()

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
        # print('************* xmin: ', xmin)
        # print('************* xmin: ', xmax)

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

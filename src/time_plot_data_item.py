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


class TimePlotDataTable():
    """
    
    Use meta classes for this...?
    
    TODO:
        * change the data_table initialization statement
        * implement response to len (maybe change len(..) to get length)
        * implement append_value (and change in time_plot_gui)
        * implement get_plot_data_item (and change in time_plot_gui)
        
    
    """
    
    
    def __init__(self, *args, **kwargs):
        self.dct = dict(*args, **kwargs)
        
    def __len__(self):
        return len(self.dct)
        
    def update(self, *args, **kwargs):
        self.dct.update(*args, **kwargs)
        
    def get(self, id_nr):
        return self.dct[id_nr]
        
    def keys(self, *args, **kwargs):
        return self.dct.keys(*args, **kwargs)
        
    def values(self, *args, **kwargs):
        return self.dct.values(*args, **kwargs)
    
    def items(self, *args, **kwargs):
        return self.dct.items(*args, **kwargs)
    
    def pop(self, id_nr):
        return self.dct.pop(id_nr)
    
    def get_plot_data_item(self, id_nr):
        return self.dct[id_nr].get_plot_data_item()
    
    def append_value(self, id_nr, val, time_val):
        self.dct[id_nr].append_value(val, time_val)

# ===========================================================================
# 
# ===========================================================================

class TimePlotDataItem(JSONFileHandler):
    """wraps the pq.PlotDataItem class to extend functionality

    Main functionality enhancement is that PlotDataItem data can now be
    extended by providing a single value. Internal functionality will take care
    of generating corresponding time value and appending the the Data object of
    PlotCurveItem.
    Furthermore, this class provides loading and saving capabilities for
    storing data in json files.


    Parameter
    ---------
    data_fn : str
        filename of data file
    id_nr : int 
        data line identification number 
    absolute_time : float
        absolute time value to sync data line values to other data line objects
    do_autosave : bool
        flag to specify if data are autosaved or not
    

    TO INCLUDE:
        * automatic saving mechanism
        
    
    Functions including data handling
        * append_value:     get_data, .. , set_data
        * get_data:         pdi.getData
        * get_time_data:    get_data
        * get_ydata:        get_data
        * set_data:         pdi.setData
        * clear_data:       set_data
        * store_data:       get_data -> save
        * recall_data:      load -> set_data

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
        self._init_data_objects(absolute_time)

    def _compose_data_name(self):
        return TimePlotDataItem.DATA_NAME.format(self.id_nr)

    def _init_data_objects(self, absolute_time):
        # self._t = []
        # self._y = []
        
        if absolute_time == None:
            self.absolute_time = time.time()
        else:
            self.absolute_time = absolute_time

    def reset_absolute_time(self, absolute_time):
        self.absolute_time = absolute_time

    def get_plot_data_item(self):
        """returns the pg.PlotDataItem"""
        return self.pdi

    def append_value(self, val, time_val):
        """adds value to pg.PlotDataItem data array"""
        
        # t, y = self.get_data()
        # t = np.append(t, time_val - self.absolute_time)
        # y = np.append(y, val)
        # self.set_data(t,y)
        
        # self._t.append(time_val - self.absolute_time)
        # self._y.append(val)
        # self.set_plot_data(self._t, self._y)
        
        t,y = self.get_data()
        t = np.append(t, time_val - self.absolute_time)
        y = np.append(y, val)
        self.set_data(t,y)
        
        if self.do_autosave:
            if len(t)%self.autosave_nr == 0:
                self.store_data()

    def get_plot_data(self):
        """returns the pg.PlotDataItem time and data arrays"""
        # t,y = self.pdi.getData()
        # t = t.tolist(); y = y.tolist()
        # return t,y
        return self.pdi.getData()
        
    def set_plot_data(self, *args, **kwargs):
        """replaces data in pg.PlotDataItem with provided data array"""
        self.pdi.setData(*args, **kwargs)
        
    # def get_data_(self):
    #     """returns the pg.PlotDataItem time and data arrays
        
    #     **obsolete**
        
    #     """
    #     # return self.pdi.getData()
    #     return self._t, self._y
    
    def get_data(self):
        """returns the pg.PlotDataItem time and data arrays"""
        return self.pdi.xData, self.pdi.yData
    
    def get_time_data(self):
        """returns the pg.PlotDataItem time value array"""
        return self.get_data()[0]

    def get_ydata(self):
        """returns the pg.PlotDataItem data value array"""
        return self.get_data()[1]

    def set_data(self, t ,y):
        """replaces data with provided data
        
        This function replaces the data lists present in this class and the 
        data in pq.PlotDataItem. This is because this function is used to 
        initialize the data structure at the beginning.
        
        """
        # self._t = t
        # self._y = y        
        # self.set_plot_data(t, y)
        self.pdi.setData(t, y)

    def clear_data(self):
        """clears all data present in this data object"""
        self.set_data([],[])

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
        # t = t.tolist(); y = y.tolist()
        data_dct = {
            # 't': self._t,
            # 'y': self._y,
            't': t.tolist(),
            'y': y.tolist(),
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
        
        Parameter
        ---------
        fn : str
            data filename from which data are imported.
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

    def set_alpha(self, value):
        """set alpha value in PlotDatItem
        
        Function rescales alpha value to range [0,1].
        
        Parameter
        ---------
        value : int
            alpha value must be provided as int in range 0 to 255
            
        """
        self.pdi.setAlpha(value/255., False)

    def set_width(self, width):
        """set width value in PlotDataItem
        
        Parameter
        ---------
        width : int
            
        
        """
        self.pdi.opts['pen'].setWidth(width)
        self.pdi.updateItems()

    def get_color(self, rgb=True):
        """returns color from plot data item object
        
        Function provides the color value as tuple of RGB values or as QColor
        object depending on how the rgb-flag is set. This double functionality
        is required to make the function interface seamlessly with the 
        _open_color_dialog function in LineSettingsQWidgetAction
        
        Parameter
        ---------
        rgb : bool
            flag indicates if color value is returned as RGB tuple (rgb=True)
            or as QColor (rgb=False).
            
        """
        if rgb:
            return self.pdi.opts['pen'].color().getRgb()
        else:
            return self.pdi.opts['pen'].color()
        
    def set_color(self, color):
        """set given color in plot data item object
        
        Function accepts QColor object or tuple of form (int, int, int, int).
        
        Parameter
        ---------
        color : QColor, tuple
            represents color value passed to plot data item. Color needs to be 
            provided as QColor or as tuple representing an RGB value (e.g. 
            (int, int, int, int)).
            
        """
        if type(color) is tuple:
            qcolor = QColor()
            qcolor.setRgb(*color)
        elif type(color) is QColor:
            qcolor = color
        else:
            raise TypeError(
                'color type not valid: {} '.format(type(color))
            )
        self.pdi.opts['pen'].setColor(qcolor)
        
    def update_color_from_dialog(self, color_dialog):
        """update color value of plot data item based on response from 
        QColorDialog 
        
        This funciton is part of the machinery to select color from 
        QColorDialog to update the plot data item color value. The variable 
        type depends on which button is clicked in the color dialog box.
        
        Parameter
        ---------
        color_dialog : QColor, QColorDialog
            variable contains color information from QColorDialog. 
            
        """
        if type(color_dialog) is QColor:
            self.set_color(color_dialog)
        elif type(color_dialog) is QColorDialog:
            self.set_color(color_dialog.currentColor())
        else:
            raise TypeError(
                'color_dialog variable type not known: {} '.format(
                    type(color_dialog)
                )
            )
        self.pdi.updateItems()

# ============================================================================
# 
# ============================================================================

class PlotDataItemV2(pg.PlotDataItem):
    """Child class customizes pyqtgraph.PlotDataItem

    This child class is designed to act as replacement for a PlotDataItem class
    and should therefore be able to neatlessly interface with the other
    pyqtgraph plot objects (e.g. ViewBox, PlotItem, PlotWidget)

    This class overwrites:
        * getData() to introduce local fft mode


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

    # def get_color(self):
    #     return self.opts['pen'].color().getRgb()

    # def update_width(self, value):
    #     # /255
    #     self.opts['pen'].setWidth(value)
    #     self.updateItems()

    # def update_color(self, color_dialog):
    #     if type(color_dialog) is QColor:
    #         self.opts['pen'].setColor(color_dialog)
    #     else:
    #         self.opts['pen'].setColor(color_dialog.currentColor())
    #     self.updateItems()

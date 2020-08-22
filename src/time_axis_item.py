#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TimeAxisItem is used to cutomize time axis of the TimePlotGui object.



"""
__version__ = "1.0.0"


import datetime
import time

import numpy as np
import pyqtgraph as pg



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

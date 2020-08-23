#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DummyDevice class is used to mock hardware devices in python. 

DummyDevice returns values on calling the get_value function. Signal form, 
amplitude and frequency can be customized through the corresponding
setter and getter function



Example::
    >>> dd = DummyDevice(signal_form='sin')
    >>> dd.set_frequency(0.5)

"""

import time
import numpy as np



class DummyDeviceException(Exception):
    pass


class DummyDevice():
    """Dummy class generates signal values and returns them on calling get_value
    
    Signal can be customized through dedicated setter and getter functions
    """
    
    def __init__(self, signal_form='sawtooth', frequency=0.1, xmin=-1, xmax=1):
        self.xmin = xmin
        self.xmax = xmax
        self.frequency = frequency    #s
        self.signal_form = signal_form
        self.time0 = time.time()
        
    def _calc_value(self):
        if self.signal_form == 'random':
            return self._calc_random()
        elif self.signal_form == 'sawtooth':
            return self._calc_sawtooth()
        elif self.signal_form == 'sin':
            return self._calc_sin()
        elif self.signal_form == 'xsin':
            return self._calc_xsin()
        elif self.signal_form == 'linear':
            return self._calc_straight_line()
        elif self.signal_form == 'sinx':
            return self._calc_sinx()
        else:
            raise DummyDeviceException('signal_form variable not know')
    
    def _calc_random(self):
        dx = self.xmax - self.xmin
        return self.xmin + dx*np.random.rand()
    
    def _calc_sawtooth(self):
        dx = self.xmax - self.xmin
        return  self.xmin + (time.time()*self.frequency % dx)
    
    def _calc_sin(self):
        dx = self.xmax - self.xmin
        return dx * np.sin(time.time()*self.frequency)
    
    def _calc_xsin(self):
        dx = self.xmax - self.xmin
        return (time.time()-self.time0)*dx * np.sin(time.time()*self.frequency)
    
    def _calc_sinx(self):
        dx = self.xmax - self.xmin
        return dx * np.sin(time.time()*self.frequency) / (time.time()-self.time0)
        
    def _calc_straight_line(self):
        return time.time()-self.time0
        
    
    def get_value(self, verbose=False):
        val = self._calc_value()
        if verbose is True: print(val)
        return val
    
    def set_frequency(self, f):
        self.frequency = f
        
    def get_frequency(self):
        return self.frequency



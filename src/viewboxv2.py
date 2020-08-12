#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thur Aug 6 14:42:02 2020

"""

import os
from os import path
import json
import numpy as np
import pyqtgraph as pg

class ViewBoxV2(pg.ViewBox):
    """
    Alternative version of viewbox that allows autopan to work as desired without directly
    changing the source code
    """
    def __init__(self, parent=None, border=None, lockAspect=False, enableMouse=True, invertY=False,
                enableMenu=True, name=None, invertX=False):
        super().__init__(parent=parent)

    def updateAutoRange(self):
        ## Break recursive loops when auto-ranging.
        ## This is needed because some items change their size in response
        ## to a view change.
    #    print(self.state['viewRange'] == self.viewRange())
        # print('\n updateAutoRange \n')
    #    print(self.state)
        if self._updatingRange:
            return

        self._updatingRange = True
        try:
            targetRect = self.viewRange()
            if not any(self.state['autoRange']):
                return

            fractionVisible = self.state['autoRange'][:]
            for i in [0,1]:
                if type(fractionVisible[i]) is bool:
                    fractionVisible[i] = 1.0

            childRange = None

            order = [0,1]
            if self.state['autoVisibleOnly'][0] is True:
                order = [1,0]

            args = {}
            for ax in order:
                if self.state['autoRange'][ax] is False:
                    continue
                if self.state['autoVisibleOnly'][ax]:
                    oRange = [None, None]
                    oRange[ax] = targetRect[1-ax]
                    childRange = self.childrenBounds(frac=fractionVisible, orthoRange=oRange)

                else:
                    if childRange is None:
                        childRange = self.childrenBounds(frac=fractionVisible)
                #print(childRange)
                ## Make corrections to range
                xr = childRange[ax]
                # print(f"ChildRange: {xr}")
                # print(f"target rect {targetRect}")
                if xr is not None:
                    if self.state['autoPan'][ax]:
                        if not ax:
                            x = xr[1]
                            width = targetRect[ax][1]-targetRect[ax][0]
                            childRange[ax] = [x-width, x]
                        else:
                            x = sum(xr) * 0.5
                            w2 = (targetRect[ax][1]-targetRect[ax][0]) / 2.
                            childRange[ax] = [x-w2, x+w2]
                # if xr is not None:
                #     if self.state['autoPan'][ax]:
                #         if self.state['data_added'] and not ax:
                #             x = self.state['newest_value']
                #  #           data_added = [0, 0]
                #  #           data_added[ax] = False
                #  #           data_added[(ax+1)%2] = self.state['data_added'][(ax+1)%2]
                #             self.state.update({'data_added': False})
                #         else:
                #             x = targetRect[ax][1]
                #         width = targetRect[ax][1]-targetRect[ax][0]
                #         #x = sum(xr) * 0.5
                #         #w2 = (targetRect[ax][1]-targetRect[ax][0]) / 2.
                #         #childRange[ax] = [x-w2, x+w2]
                #         childRange[ax] = [x-width, x]
                    else:
                        padding = self.suggestPadding(ax)
                        wp = (xr[1] - xr[0]) * padding
                        childRange[ax][0] -= wp
                        childRange[ax][1] += wp
                    targetRect[ax] = childRange[ax]
                    args['xRange' if ax == 0 else 'yRange'] = targetRect[ax]
            if len(args) == 0:
                return
            args['padding'] = 0
            args['disableAutoRange'] = False

             # check for and ignore bad ranges
            for k in ['xRange', 'yRange']:
                if k in args:
                    if not np.all(np.isfinite(args[k])):
                        r = args.pop(k)
                        #print("Warning: %s is invalid: %s" % (k, str(r))

            self.setRange(**args)
        finally:
            self._autoRangeNeedsUpdate = False
            self._updatingRange = False



# class PlotItemV2(pg.plotItem):
#     """
#     Alternative version of plotItem class to initialize the alternative version of ViewBox class
#     """

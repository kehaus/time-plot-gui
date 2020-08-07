#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 


* use unix time as absolute time measure
* save time data for every device seperately
* save parameter in json and data in csv

Example:

>>> wt = WorkerTask(func1)    #func1 needs to be defined already
>>> q = queue.Queue()
>>> q.put(wt)                # load task into queue
>>> w(q)
>>> w.start()                # start thread

"""


import threading
import queue
import csv
import time
import inspect



# ===========================================================================
# Exception class
# ===========================================================================        
class WorkerThreadException(Exception):
    """ """
    pass

class WorkerTaskException(Exception):
    """ """
    pass


# ===========================================================================
# Worker Thread
# ===========================================================================        

class WorkerThread(threading.Thread):
    """creates a thread to 



    Example:
        >>> w = WorkerTask(func1, save=True, continuous=True)
        >>> q = queue.Queue()
        >>> q.put(w)
        >>> ww = WorkerThread(q)
        >>> ww.start()

    To stop:
        >>> ww.stop()

     """

    SLEEP_TIME = 0.001

    def __init__(self, q=None):
        super(WorkerThread, self).__init__()
        if q is None: 
            q=queue.Queue()
        self.q = q
        self._stop_thread = True
        self.sleep_time = WorkerThread.SLEEP_TIME


    def run(self):

        self._stop_thread = False
        while not self._stop_thread:
            if not self.q.empty():    
                self.process_task()
            time.sleep(self.sleep_time)

    def stop(self):
        self._stop_thread = True

    def put(self, w):
        if not isinstance(w, WorkerTaskBase):
            raise WorkerThreadException('argument needs to be WorkerTask object: {}'.format(w))
        else:
            self.q.put(w)


    def process_task(self):
        """removes task from queue and processes it"""
        task = self.q.get()
        if task.continuous: self.q.put(task)
        task.do_task()


# ===========================================================================
# Worker Task
# ===========================================================================        

class WorkerTaskBase(object):
    """ 
    Represents a function call which is handed to the WorkerThread
    
    
    
    Example
    >>> def func():
    >>>     print('hello')
    >>>
    >>> wt = WorkerTaskBase(func, continuous=True)
    
    
    """
    COUNT = 0

    def __init__(self, 
                 func, 
                 args=None, 
                 kwargs=None, 
                 continuous=False,
                 callback=None,
                 ):
        WorkerTaskBase.COUNT += 1
        self.continuous = continuous

        self.func = self._check_func(func)
        self.args = self._check_args(args)
        self.kwargs = self._check_kwargs(kwargs)
        self.callback = self._check_callback(callback)

    def _check_func(self, func):
        if callable(func) != True:
            raise WorkerTaskException('func needs to be callable object: {}'.format(func))
        return func
    
    def _check_callback(self, callback):
        if callback is None:
            return callback
        if callable(callback) != True:
            raise WorkerTaskException('callback needs to be callable object: {}'.format(callback))
        return callback
    

    def _check_args(self, args):
        """verify if args is list-like by checking if it is iterable"""
        if args == None:
            args = []
        try:
            for i in args:
                pass
        except TypeError:
            raise WorkerTaskException('args is not a list-like object: {}'.format(args))
        return args

    def _check_kwargs(self, kwargs):
        if kwargs == None:
            kwargs = {}
        if type(kwargs) != dict:
            raise WorkerTaskException('kwargs needs to be of type dict: {}'.format(kwargs))
        return kwargs


    def do_task(self):

        self.rtn = self.func(*self.args, **self.kwargs)
        if self.callback is not None: 
            self.callback(self.rtn)
#        return self.rtn
    

# ===========================================================================
# Depricated
# ===========================================================================        

# class WorkerTask(DataSet):
#     """ """

#     COUNT = 0
# #    DEFAULT_FILE_HEADER = [
# #        'time',
# #        'variable'
# #    ]

#     def __init__(self, 
#                  func, 
#                  args=None, 
#                  kwargs=None, 
#                  continuous=False, 
#                  save=False, 
#                  plot=False,
#                  base_name=None):
#         super().__init__(base_name=base_name)
#         WorkerTask.COUNT += 1
#         self.continuous = continuous
        # self.continuous = self._check_continous_flag
#         self.save = bool(save)
#         self.fn_base = 'workertask{:d}'.format(WorkerTask.COUNT)
#         self.plot = plot

#         self.func = self._check_func(func)
#         self.args = self._check_args(args)
#         self.kwargs = self._check_kwargs(kwargs)

#     def _check_func(self, func):
#         if callable(func) != True:
#             raise WorkerTaskException('func needs to be callable object')
#         return func

#     def _check_args(self, args):
#         if args == None:
#             args = []
#         if type(args) != list:
#             raise WorkerTaskException('args needs to be of type list')
#         return args

#     def _check_kwargs(self, kwargs):
#         if kwargs == None:
#             kwargs = {}
#         if type(kwargs) != dict:
#             raise WorkerTaskException('kwargs needs to be of type dict')
#         return kwargs


#     def plot_data(self):
#         pass

#     def do_task(self):

#         self.rtn = self.func(*self.args, **self.kwargs)

#         if self.save != False:
#             self.save_data_point(self.rtn)

#         if self.plot != False:
#             self.plot_data()
#         return

    # def _check_continuous_flag(self, continuous):
    #     if continuous is True or continuous is False:
    #         return continuous
    #     if continuous is None:
    #         return False
        
    #     try:
    #         if float(continuous).is_integer():
    #             return float(continuous)
    #         else:
    #             raise WorkerTaskException('continous needs to be a boolean or an integer')
    #     except ValueError:
    #         raise WorkerTaskException('continous flag needs to be a boolean or an integer')



### Dataset class






# ===========================================================================
# Test function
# ===========================================================================        

def func1():
    return 'func1'

def func2(x,y, z=8):
    print('func2')
    print('x: ', x, 'y: ', y, 'z: ', z)
    return

def func3(v=33, w=55, z=9):
    print('func3')
    print('v: ', v, 'w: ', w, 'z: ',z)
    return


# ===========================================================================
# main function
# ===========================================================================        
if __name__ == "__main__":
    wt = WorkerTaskBase(func3, continuous=True)
    q = queue.Queue()
    q.put(wt)
    w = WorkerThread(q)
#    w.start()





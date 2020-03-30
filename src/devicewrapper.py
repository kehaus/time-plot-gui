#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 23:42:27 2020


TODO:
    * signal back to DeviceWrapper from WorkerThread when thread is terminated

"""



import os
import threading
import queue


from worker_thread import WorkerThread, WorkerTask



# ===========================================================================
# Exception class
# ===========================================================================        
class DeviceWrapperException(Exception):
    pass


# ===========================================================================
# DeviceWrapper class
# ===========================================================================        

class DeviceWrapper():
    """Wrapper class for device object
    
    
    Class provides framework to directly call device functions and attributes
    while device is part of a worker thread in the background.
    
    
    """
    
    def __init__(self, device):
        self.d = device
        self.thread_runs = False
        
        self._create_worker_thread()
        
    def __getattr__(self, name):
        if hasattr(self.d, name):
            if self.thread_runs:
                self.func_name = name
                return self.send_worker_task
            else:
                return getattr(self.d, name)
        else:
            raise AttributeError
        
    def _create_worker_thread(self):
        q = queue.Queue()
        self.wt = WorkerThread(q)
        
    def start(self):
        """starts thread"""
        if not self.thread_runs:
            self.wt.start()
            self.thread_runs = True
        else:
            raise DeviceWrapperException('Thread runs already.')
        
    def stop(self):
        """stops thread"""
        if self.thread_runs:
            self.wt.stop()
            self.thread_runs = False
        else:
            raise DeviceWrapperException('Thread is not running.')
        
    def send_worker_task(self, *args, **kwargs):
        w = WorkerTask(
            func=self.func_name, 
            args=args, 
            kwargs=kwargs
        )
        self.wt.put(w)
        





# ===========================================================================
# Dummy classes
# ===========================================================================        

class C():
    """Dummy class, counts either up or down when count is called """
    
    def __init__(self):
        self.i = 0
        self.count_direction = 1
    
    def count(self):
        self.i += 1 * self.count_direction
        print('i: ', self.i)
        
    def get_count(self):
        return self.i
        
    def reverse(self):
        self.count_direction *= -1

# ===========================================================================
# main
# ===========================================================================        
if __name__ == "__main__":
    c = C()
    
    wd = DeviceWrapper(c)
    
    pass
       


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 23:42:27 2020


TODO:

"""



import os
import threading
import queue
import time


from workerthread import WorkerThread, WorkerTaskBase



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
    
    
    Example:
        >>> d = SomeDevice()
        >>> d.some_function()
        5
        >>> dw = DeviceWrapper(d)
        >>> dw.some_function()
        5
        
        
    """
    
    def __init__(self, device):
        self.d = device        
        self._create_worker_thread()
        
    def __getattr__(self, name):
        """redirects method and attribute calls to device object
        
        
        """
        if hasattr(self.d, name):
            if self.thread_is_alive():
                self.func_name = getattr(self.d, name)
                return self._send_worker_task
            else:
                return getattr(self.d, name)
        else:
            raise AttributeError
        
    def _create_worker_thread(self):
        """initialzes the workerthread """
        q = queue.Queue()
        self.wt = WorkerThread(q)
        
    def start(self):
        """starts workerthread"""
        if not self.thread_is_alive():
            self.wt.start()
        else:
            raise DeviceWrapperException('Thread runs already.')
        
    def stop(self):
        """stops workerthread"""
        if self.thread_is_alive():
            self.wt.stop()
        else:
            raise DeviceWrapperException('Thread is not running.')
    
    def thread_is_alive(self):
        return self.wt.is_alive()
        
    def _send_worker_task(self, *args, **kwargs):
        w = WorkerTaskBase(
            func=self.func_name, 
            args=args, 
            kwargs=kwargs,
            callback=self._callback
        )
        self.wt.put(w)
        self.wait_for_callback = True
        
        while self.wait_for_callback:
            time.sleep(0.1)
        return self.rtn
        
            
    def _callback(self, return_args):
        """helper function to retrieve return value from WorkTask object
        
        This function is part of the callback mechanism to retrieve the return
        value from the WorkerTask object function call initiated by the _
        send_worker_task function
        
        """
        self.rtn = return_args
        self.wait_for_callback = False






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
    
    dw = DeviceWrapper(c)
    dw.wt.q.put(WorkerTaskBase(dw.d.count, continuous=True))
#    dw.start()
    
    pass
       


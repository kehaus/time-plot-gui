#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 


* use unix time as absolute time measure
* save time data for every device seperately
* save parameter in json and data in csv

Example:

>>> wt = WorkerTask(func1)	#func1 needs to be defined already
>>> q = queue.Queue()
>>> q.put(wt)				# load task into queue
>>> w(q)
>>> w.start()				# start thread

"""


import threading
import queue
import csv
import time
import inspect

#from ..util.general_util import DataSet, TimeFormatter, CSVHandler, JSONHandler
from general_util import DataSet, TimeFormatter, CSVHandler, JSONHandler



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
	"""



	Example:
		>>> w = WorkerTask(func1, save=True, continuous=True)
		>>> q = queue.Queue()
		>>> q.put(w)
		>>> ww = WorkerThread(q)
		>>> ww.start()

	To stop:
		>>> ww.stop()

	 """

	SLEEP_TIME = 0.1

	def __init__(self, q):
		super(WorkerThread, self).__init__()
		self.q = q
		self._stop = True
		self.sleep_time = WorkerThread.SLEEP_TIME


	def run(self):

		self._stop = False
		while not self._stop:
			if not self.q.empty():	
				self.process_task()
			time.sleep(self.sleep_time)

	def stop(self):
		self._stop = True

	def put(self, w):
		if not isinstance(w, WorkerTask):
			raise WorkerThreadException('argument needs to be WorkerTask object')
		else:
			self.q.put(w)


	def process_task(self):
		task = self.q.get()
		if task.continuous: self.q.put(task)
		task.do_task()


# ===========================================================================
# Worker Task
# ===========================================================================        

class WorkerTaskBase(object):
	""" """
	def __init__(self, obj, attr):
		""" """
		self.continuous = False
		self.args = []
		self.kwargs = {}
		self.obj = obj
		self.obj_attr = attr
#		print('callable: ', callable(getattr(obj, attr)))
#		print('_check:', self._check_func(getattr(obj, attr)))
		self.obj_attr = self._check_func(getattr(obj, attr))


		



	def _check_func(self, func):
		if callable(func) != True:
			raise WorkerTaskException('func needs to be a callable object')
		return func

	def load_args_kwargs(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs

	def do_task(self):
		rtn = self.obj_attr(*self.args, **self.kwargs)
		return rtn


class WorkerTask(DataSet):
	""" """

	COUNT = 0
#	DEFAULT_FILE_HEADER = [
#		'time',
#		'variable'
#	]

	def __init__(self, 
				 func, 
				 args=None, 
				 kwargs=None, 
				 continuous=False, 
				 save=False, 
				 plot=False,
                 base_name=None):
		super().__init__(base_name=base_name)
		WorkerTask.COUNT += 1
		self.continuous = continuous
		self.save = bool(save)
		self.fn_base = 'workertask{:d}'.format(WorkerTask.COUNT)
		self.plot = plot

		self.func = self._check_func(func)
		self.args = self._check_args(args)
		self.kwargs = self._check_kwargs(kwargs)

	def _check_func(self, func):
		if callable(func) != True:
			raise WorkerTaskException('func needs to be callable object')
		return func

	def _check_args(self, args):
		if args == None:
			args = []
		if type(args) != list:
			raise WorkerTaskException('args needs to be of type list')
		return args

	def _check_kwargs(self, kwargs):
		if kwargs == None:
			kwargs = {}
		if type(kwargs) != dict:
			raise WorkerTaskException('kwargs needs to be of type dict')
		return kwargs


	def plot_data(self):
		pass

	def do_task(self):

		self.rtn = self.func(*self.args, **self.kwargs)

		if self.save != False:
			self.save_data_point(self.rtn)

		if self.plot != False:
			self.plot_data()
		return


### Dataset class





### Examples usage case

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


if __name__ == "__main__":
    wt = WorkerTask(func1, continuous=True)
    q = queue.Queue()
    w = WorkerThread(q)





#!/usr/bin/python

#TODO: .commsrc
#TODO: globals and thread locals
#TODO: with contexts
#TODO: multiline splitting

import re
import sys
import json
import socket
import syslog
import inspect
import logging
import threading
import traceback
import logging.handlers as handlers

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())
logger.propagate = False

syslog_handler = None
def log_to_syslog(address=('localhost', 514), facility=syslog.LOG_USER, level=logging.DEBUG):
	global syslog_handler
	if syslog_handler:
		syslog_handler.close()
		logger.removeHandler(syslog_handler)
	syslog_handler = handlers.SysLogHandler(address=address, facility=facility) 
	syslog_handler.setLevel(level)
	logger.addHandler(syslog_handler)

stream_handler = None
def log_to_stdout(level=logging.INFO, stream=sys.stdout):
	global stream_handler
	if stream_handler:
		stream_handler.close()
		logger.removeHandler(stream_handler)
	stream_handler = logging.StreamHandler(stream)
	stream_handler.setLevel(level)
	logger.addHandler(stream_handler)

#TODO: Reuse _emit instead of manual message fabrication
_monitor_cache = threading.local()
def monitor(name, new_value, log_method='warn'):
	if not hasattr(_monitor_cache, name):
		setattr(_monitor_cache, name, None)
	old_value = getattr(_monitor_cache, name)
	if old_value != new_value:
		msg = {'_msg':"monitor: %s changed"%name, '_level':log_method, 'from':old_value, 'to':new_value}
		getattr(logger, log_method)(": @cee: %s"%json.dumps(msg))
	setattr(_monitor_cache, name, new_value)

interpreter_global = {}
thread_local = threading.local()
def _emit(msg=None, level=None, **kwargs):
	"""_emit must be called by an intermediary function (.f_back.f_back)"""
	log = {}
	log.update(interpreter_global)
	log.update(thread_local.__dict__)
	log.update(kwargs)
	log['_msg'] = ""
	if level:
		log['_level'] = level
	if isinstance(msg, BaseException):
		log['_exception'] = traceback.format_exc(msg)
	elif msg:
		caller_globals = inspect.currentframe().f_back.f_back.f_globals
		caller_locals  = inspect.currentframe().f_back.f_back.f_locals
		for fgmnt in re.split(r"({[^{}]+})", msg):
			match = re.match(r"{(.*)}", fgmnt)
			if match:
				key = match.group(1)
				if key not in log:
					log[key] = eval(key, caller_globals, caller_locals)
				log['_msg'] += str(log[key])
			else:
				log['_msg'] += str(fgmnt)
	return ": @cee: %s"%json.dumps(log)

def set_local(key, value):
	setattr(thread_local, key, value)

class local(object):
	def __init__(self, fields):
		self.old = thread_local
		self.new = fields
	def __enter__(self):
		global thread_local
		thread_local = threading.local()
		for key, value in self.old.__dict__.items():
			setattr(thread_local, key, value)
		for key, value in self.new.items():
			setattr(thread_local, key, value)
	def __exit__(self, type, value, traceback):
		global thread_local
		thread_local = self.old

def debug(msg=None, **kwargs):
	logger.debug(_emit(msg=msg,level='debug',**kwargs))
def info(msg=None, **kwargs):
	logger.info(_emit(msg=msg,level='info',**kwargs))
def warn(msg=None, **kwargs):
	logger.warn(_emit(msg=msg,level='warn',**kwargs))
def error(msg=None, **kwargs):
	logger.error(_emit(msg=msg,level='error',**kwargs))
def fatal(msg=None, **kwargs):
	logger.fatal(_emit(msg=msg,level='fatal',**kwargs))

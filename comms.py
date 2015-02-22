#!/usr/bin/python

#TODO: .commsrc
#TODO: globals and thread locals
#TODO: with contexts
#TODO: multiline splitting

import re
import json
import socket
import syslog
import inspect
import logging
import threading
import traceback
import logging.handlers as handlers

logger = logging.getLogger(__name__)

syslog_handler = None
def to_syslog(address=('localhost', 514), facility=syslog.LOG_USER):
	global syslog_handler
	if syslog_handler:
		syslog_handler.close()
		logger.removeHandler(syslog_handler)
	syslog_handler = handlers.SysLogHandler(address=address, facility=facility) 
	logger.addHandler(syslog_handler)
	logger.setLevel(logging.DEBUG)

def to_stdout(level=logging.INFO):
	handler = logging.StreamHandler()
	handler.setLevel(level)
	logger.addHandler(handler)

interpreter_global = {}
thread_local = threading.local()
def _emit(msg=None, level=None, **kwargs):
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
		caller_globals = inspect.currentframe().f_back.f_globals
		caller_locals  = inspect.currentframe().f_back.f_locals
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

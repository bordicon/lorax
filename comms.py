#!/usr/bin/python

#TODO: .commsrc
#TODO: globals and thread locals
#TODO: with contexts
#TODO: multiline splitting

import re
import inspect

def emit(msg=None, **kwargs):
	caller_globals = inspect.currentframe().f_back.f_globals
	caller_locals  = inspect.currentframe().f_back.f_locals
	kwargs['msg'] = ""
	for fgmnt in re.split(r"({[^{}]+})", msg):
		match = re.match(r"{(.*)}", fgmnt)
		if match:
			key = match.group(1)
			if key not in kwargs:
				kwargs[key] = eval(key, caller_globals, caller_locals)
			kwargs['msg'] += str(kwargs[key])
		else:
			kwargs['msg'] += str(fgmnt)
	return kwargs

def debug(msg=None, **kwargs):
	emit(msg=msg,level='debug',**kwargs)

def info(msg=None, **kwargs):
	emit(msg=msg,level='info',**kwargs)

def warn(msg=None, **kwargs):
	emit(msg=msg,level='warn',**kwargs)

def error(msg=None, **kwargs):
	emit(msg=msg,level='error',**kwargs)

def fatal(msg=None, **kwargs):
	emit(msg=msg,level='fatal',**kwargs)

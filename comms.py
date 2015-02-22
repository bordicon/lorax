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
import logging.handlers

logger = logging.getLogger(__name__)

handler = None
def to_syslog(address=('localhost', 438), facility=None):
	global handler
	if handler:
		handler.close()
		logger.removeHandler(handler)
	handler = logging.handlers.SysLogHandler(address=address, facility=facility)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

def _extract(msg=None, **kwargs):
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
	return ": @cee: %s"%json.dumps(kwargs)
format
def debug(msg=None, **kwargs):
	logger.debug(_extract(msg=msg,**kwargs))
def info(msg=None, **kwargs):
	logger.info(_extract(msg=msg,**kwargs))
def warn(msg=None, **kwargs):
	logger.warn(_extract(msg=msg,**kwargs))
def error(msg=None, **kwargs):
	logger.error(_extract(msg=msg,**kwargs))
def fatal(msg=None, **kwargs):
	logger.fatal(_extract(msg=msg,**kwargs))
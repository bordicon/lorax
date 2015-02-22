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
import traceback
import logging.handlers as handlers

logger = logging.getLogger(__name__)

syslog_handler = None
def to_syslog(address=('localhost', 438), facility=None):
	global syslog_handler
	if syslog_handler:
		syslog_handler.close()
		logger.removeHandler(syslog_handler)
	syslog_handler = handlers.SysLogHandler(address=address,
											facility=syslog.LOG_USER) 
	logger.addHandler(syslog_handler)
	logger.setLevel(logging.DEBUG)

def _extract(msg=None, **kwargs):
	kwargs['msg'] = ""
	if isinstance(msg, BaseException):
		kwargs['exception'] = traceback.format_exc(msg)
	elif msg:
		caller_globals = inspect.currentframe().f_back.f_globals
		caller_locals  = inspect.currentframe().f_back.f_locals
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
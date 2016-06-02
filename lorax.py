#!/usr/bin/python

#TODO: See if it's worth conforming to CEE (https://fedorahosted.org/lumberjack/)
#TODO: format/parse can be simplified further, but want to keep diff small.
#TODO: Switch log_to_stdout to use unstructured formatter by default
#TODO: Add timestamps to log_to_stdout default formatter
#TODO: Add support for *args to logging calls to behave just like basestring#format

import os
import sys
import json
import string
import socket
import syslog
import logging
import threading
import traceback
from datetime import datetime
import logging.handlers as handlers

## Setup Globals
# Python 2.6.6 doesn't have logging.NullHandler
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# logger to emit structured log events to
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(NullHandler())
logger.propagate = False

# Storage for attributes shared by all events in thread/process
process_attributes = {}
thread_attributes = threading.local()

# Sadly, this is the simplest way NOT to log structured output.
class UnstructuredFormatter(logging.Formatter):
    def format(self, record):
        return json.loads(record.msg)['_msg']

# A formatter for logging unstructured messages with a timestamp
class UnstructuredTimestampFormatter(logging.Formatter):
    def format(self, record):
        record = json.loads(record.msg)
        record['_time'] = self.reformatTime(record['_time'])
        return '\n[%s : %s] %s ' % (
            record['_time'], 
            record['_level'].upper(), 
            record['_msg'])
    def reformatTime(self, record_time):
        timestamp = datetime.strptime(record_time[0:19],"%Y-%m-%dT%H:%M:%S")
        return timestamp.strftime("%Y%m%dT%H%M%SZ")

## Core Methods
def format(record, **overrides):
    """ Convert a jsonizable dictionary into a structured log event """
    try:
        event = {}
        event.update(process_attributes)
        event.update(thread_attributes.__dict__)
        event.update(record)
        event.update(overrides)
        for k,v in event.items():
            try:
                json.dumps(v)
            except:
                event[k] = str(v)
        return json.dumps(event)
    except:
        return traceback.format_exc()

def parse(msg, **kwargs):
    """ Convert a regular string or formattable string into a structured log record.
        Safer than log.warn("foo {foo}".format(foo='foo')) since it won't throw
        an exception somewhere undesirable (like an error handler)

        Essentially a version of python's 'format' call that outputs a structured
        log record and records exceptions instead of throwing them.

        Example:

        parse('User {name} logged in', name='phillip')
        # => {'_msg':'User phillip logged in', 'name':'phillip', '_host':...}
    """
    record = {'_msg':msg}
    try:
        record['_host'] = socket.gethostname()
        record['_time'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        record['_tname'] = threading.current_thread().name
        if isinstance(msg, basestring):
            # If it looks like a formattable string, try to format it.
            if '{' in msg and len(kwargs) > 0:
                record['_msg'] = msg.format(**kwargs)
        elif isinstance(msg, BaseException):
            # Python 2 doesn't store traceback in Exception, but it's probably on stack.
            if sys.exc_info()[1] == msg:
                record['_msg'] = traceback.format_exc()
            else:
                record['_msg'] = repr(msg)
    except:
        record['_lorax_exception'] = traceback.format_exc()
    return record

## Additional Features
def process(pname):
    """ It's too hard to inspect the running process name, so we punt and
        require it be set manually

        Example:
        #!/usr/bin/python

        import argparse

        parser = argparse.ArgumentParser(description='Site agent for GSOAP")
        parser.add_argument('-v', '--verbose', action="store_true")

        log.process('gs-agent')
        log.log_to_syslog()
        if args.verbose:
            log.log_to_stdout(level=logging.DEBUG)
        ...

    """
    process_attributes['_pname'] = pname


class local(object):
    """ Set thread-local attributes for duration of 'with' call

        Example:

        def handle_request(request):
            with lorax.local({'request.id':request.id}):
                ...

    """
    def __init__(self, fields):
        self.existing = thread_attributes
        self.temp = fields
    def __enter__(self):
        global thread_attributes
        thread_attributes = threading.local()
        for key, value in self.existing.__dict__.items():
            setattr(thread_attributes, key, value)
        for key, value in self.temp.items():
            setattr(thread_attributes, key, value)
    def __exit__(self, type, value, traceback):
        global thread_attributes
        thread_attributes = self.existing

## Just give me an API I can use!
def _log(msg, logging_method, **kwargs):
    msg = format(parse(msg, **kwargs), _level=logging_method.__name__, **kwargs)
    logging_method(msg)
    return msg
# Logging methods should return the string they logged!
def debug(msg, **kwargs):
    return _log(msg, logger.debug, **kwargs)
def info(msg, **kwargs):
    return _log(msg, logger.info, **kwargs)
def warn(msg, **kwargs):
    return _log(msg, logger.warn, **kwargs)
def error(msg, **kwargs):
    return _log(msg, logger.error, **kwargs)
def fatal(msg, **kwargs):
    return _log(msg, logger.fatal, **kwargs)

## Convenience method for logging to different sources.  Why make so hard, Python?
def log_to_syslog(host='localhost', port=None, facility=handlers.SysLogHandler.LOG_USER, level=logging.DEBUG):
    """ Aggressively try to connect to syslog by various means and on various platforms """
    handler = None
    if host == 'localhost' and port is None:
        try:
            path = next(p for p in ['/dev/log', '/var/run/syslog'] if os.path.exists(p))
            handler = handlers.SysLogHandler(address=path, facility=facility)
        except:
            pass

    if not handler:
        try:
            handler = handlers.SysLogHandler(address=(host, port or handlers.SYSLOG_TCP_PORT),
                                             facility=facility,
                                             socktype=socket.SOCK_STREAM)
        except:
            handler = handlers.SysLogHandler(address=(host, port or handlers.SYSLOG_UDP_PORT),
                                             facility=facility,
                                             socktype=socket.SOCK_DGRAM)
    handler.setLevel(level)
    formatter = logging.Formatter('lorax: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return handler

def log_to_stdout(level=logging.DEBUG, stream=sys.stdout):
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    logger.addHandler(handler)
    return handler

def log_to_file(filename, level=logging.DEBUG):
    handler = logging.FileHandler(filename)
    handler.setLevel(level)
    logger.addHandler(handler)
    return handler

def log_to_truffula(host='truffula.pvt.spire.com', port=5140, facility=handlers.SysLogHandler.LOG_USER, level=logging.DEBUG):
    handler = handlers.SysLogHandler(address=(host, port),
                                     facility=facility,
                                     socktype=socket.SOCK_DGRAM)
    handler.setLevel(level)
    hostname = socket.gethostname()
    fmt_str = '%(asctime)s ' + hostname + ' lorax: %(message)s'
    formatter = logging.Formatter(fmt=fmt_str,
                                  datefmt='%b %d %H:%M:%S')

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return handler

# Lorax
Structured Logging Micro-Framework for Python.

Why does logging have to be so noisy?  Takes Python-3 style strings (interpolation boundaries defined by {...}) and generates a json-structured log event containing the interpolated string plus a field for each variable used.

Logs to any number of conveniently defined destinations.  Conforms, roughly, to [CEE](cee.mitre.org) and [Lumberjack](https://fedorahosted.org/lumberjack/).

## Usage

```python
#!/usr/bin/python

import lorax as log

for user_id in ["1", "-1", "NaN"]:
	try:
		valid = int(user_id) > 0
		log.info("Valid user_id {user_id}: {valid}", user_id=user_id, valid=valid)
	except Exception as e:
		log.error(e)
# =>
# => {"_msg": "Valid user_id 1: True", "user_id": "1", "valid": true, "_time": "2015-04-03T19:32:33.281622Z", "_tname": "MainThread", "_level": "info", "_host": "jints-iMac.local"}
# => {"_msg": "Valid user_id -1: False", "user_id": "-1", "valid": false, "_time": "2015-04-03T19:32:33.281990Z", "_tname": "MainThread", "_level": "info", "_host": "jints-iMac.local"}
# => {"_msg": "Traceback (most recent call last):\n  File \"/Users/jint/Documents/spire/air/gs/lorax/test.py\", line 9, in <module>\n    valid = int(user_id) > 0\nValueError: invalid literal for int() with base 10: 'NaN'\n", "_time": "2015-04-03T19:32:33.282081Z", "_tname": "MainThread", "_level": "error", "_host": "jints-iMac.local"}
```

### Log to different (or multiple) locations

```python
import lorax as log

# Log to terminal
log.log_to_stdout()

# Log to local syslog
log.log_to_syslog()

# Log to remote syslog
log.log_to_syslog(host='rsyslog.company.com')

log.info("LOG EVERYWHERE!")
```

### Log data items
```
# Non-string messages are JSON encoded along with the rest of the record
log.error({'foo':1})
# => {"_host": "jints-iMac.local", "_time": "2015-05-14T17:48:15.629488Z", "_msg": {"foo": 1}, "_tname": "MainThread", "_level": "error"}

# If JSON-encoding fails, we fallback to str()
log.error(open('/tmp/foo', 'w'))
# => {"_host": "jints-iMac.local", "_time": "2015-05-14T17:48:52.508664Z", "_msg": "<open file '/tmp/foo', mode 'w' at 0x10947ff60>", "_tname": "MainThread", "_level": "error"}
```

### Additional tags
```
log.error("foo", bar=1, tag2='buz')
{"_time": "2015-05-14T17:47:54.486291Z", "bar": 1, "tag2": "buz", "_tname": "MainThread", "_level": "error", "_host": "jints-iMac.local", "_msg": "foo"}
```

### Tag all messages with process name

```python
log.process('my_script.py')

log.info("Hello")
# => '{"_time": "2015-04-03T17:39:37.873382Z", "_tname": "MainThread", "_level": "info", "_host": "jints-iMac.local", "_pname": "my_script.py", "_msg": "Hello"}'
log.warn("World")
# => '{"_time": "2015-04-03T17:40:27.928448Z", "_tname": "MainThread", "_level": "warn", "_host": "jints-iMac.local", "_pname": "my_script.py", "_msg": "World"}'
```

### Change logging level per-destination
```
log.log_to_stdout(level=logging.ERROR)
log.info(1)
log.error(1)
# => {"_host": "jints-iMac.local", "_time": "2015-05-14T17:52:27.596439Z", "_msg": 1, "_tname": "MainThread", "_level": "error"}
```

### Tag log events within block

```python

def process_loop():
	while True:
		log.info("Checking for new request")
		request = poll_for_request()
		with log.local({'request':request.id}):
			log.info("Processing request")
			process_request(request)
# =>
# => {"_host": "jints-iMac.local", "_time": "2015-04-03T17:57:38.692704Z", "_tname": "MainThread", "_level": "info", "_msg": "Checking for new request"}
# => {"_host": "jints-iMac.local", "_time": "2015-04-03T17:57:38.692963Z", "_tname": "MainThread", "_level": "info", "_msg": "Processing request", "request": "235489234"}

```

### Add custom logging handlers

```python
handler = logging.handlers.NTEventLogHandler('test.py')
lorax.logger.addHandler(handler)

# lorax.logger is a standard Python logger!
lorax.debug("This'll go to the windows event log!")
```

## FAQ

**Q: Why are long log messages are being truncated in /var/log/syslog ?**

A: Older versions of `rsyslog` impose a length limit (~2000 characters) and will cutoff extra log messages, which can break json parsing.
Upgrade rsyslog on older versions of Ubuntu (< 14.04):
```bash
sudo apt-get install python-software-properties
sudo add-apt-repository ppa:adiscon/v8-stable
sudo apt-get update
sudo apt-get install rsyslog
```
Above instructions from http://www.rsyslog.com/ubuntu-repository/

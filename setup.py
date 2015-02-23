#!/usr/bin/python

from distutils.core import setup
setup(
	name='lorax',
	version='0.1',
	author="Jesse Trutna",
	author_email="jesse@spire.com",
	data_files=[('/usr/local/bin', ['bin/lorax'])],
	py_modules=['comms']
	)


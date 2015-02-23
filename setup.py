#!/usr/bin/python

from distutils.core import setup
setup(
	name='comms',
	version='0.1',
	author="Jesse Trutna",
	author_email="jesse@spire.com",
	data_files=[('/usr/local/bin', ['bin/comms-filter'])],
	py_modules=['comms']
	)


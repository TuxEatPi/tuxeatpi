
dep:
	apt-get install python-virtualenv

env:
	virtualenv env
	env/bin/pip install RPi.GPIO



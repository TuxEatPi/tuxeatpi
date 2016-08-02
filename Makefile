
dep-dev:
	sudo apt-get install python3-virtualenv python3-pil.imagetk python3-tk male
#   Not sure of that one
#	sudo apt-get install python3-dev

env-dev:
	virtualenv --system-site-packages -p /usr/bin/python3 env
	env/bin/pip3 install -r requirements-dev.txt
	env/bin/pip3 install -r requirements.txt
	env/bin/python setup.py develop

env:
	virtualenv -p /usr/bin/python3 env
	env/bin/pip3 install RPi.GPIO

tux_example:
	env/bin/python examples/simple_tux_with_gpiosim.py


gpiosim:
	env/bin/GPIOSim &

doc-update-refs:
	rm -rf doc/source/refs/
	sphinx-apidoc -M -f -e -o doc/source/refs/ tuxeatpi/               

doc-generate:
	cd doc && make html

test-run:
	env/bin/nosetests --with-coverage tests

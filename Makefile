
#######################################
### Dev targets
#######################################
dep-dev:
	sudo apt-get install python3-virtualenv python3-pil.imagetk python3-tk
#   Not sure of that one
#	sudo apt-get install python3-dev

env-dev:
	virtualenv --system-site-packages -p /usr/bin/python3 env
	env/bin/pip3 install -r requirements-dev.txt --upgrade --force-reinstall
	env/bin/pip3 install -r requirements.txt --upgrade --force-reinstall
	env/bin/python setup.py develop

#######################################
### Virtual env targets
#######################################
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
	touch doc/build/html/.nojekyll

#######################################
### Test targets
#######################################

test-run:
	rm -rf .coverage cover/
	mkdir -p /tmp/GPIOSim
	cp -f tests/pins.ini /tmp/GPIOSim/pins.ini
	pep8 --max-line-length=100 --exclude='*.pyc' --exclude=tuxeatpi/experimental tuxeatpi
	pylint --rcfile=.pylintrc -r no tuxeatpi
	env/bin/nosetests --with-coverage --cover-html --cover-package=tuxeatpi tests -svd --with-xunit

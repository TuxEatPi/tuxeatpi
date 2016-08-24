
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

#hotword:
#	sudo apt-get install swig swig3.0 python-pyaudio python3-pyaudio sox libatlas-base-dev
#	rm -rf hotword
#	mkdir -p hotword
#	cd hotword && git clone https://github.com/Kitt-AI/snowboy.git
#	cd hotword/snowboy/ && git checkout devel
#	cd hotword/snowboy/swig/Python && make
#	cp hotword/snowboy/swig/Python/_snowboydetect.so tuxeatpi/hotword
#	cp hotword/snowboy/swig/Python/snowboydetect.py tuxeatpi/hotword
#	cp hotword/snowboy/examples/Python/snowboydecoder.py tuxeatpi/hotword
#	rm -rf hotword


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
	pep8 --max-line-length=100 --exclude='*.pyc' --exclude=tuxeatpi/experimental tuxeatpi
	pylint --rcfile=.pylintrc -r no tuxeatpi
	env/bin/nosetests --with-coverage --cover-html --cover-package=tuxeatpi -svd --with-xunit --with-html tests

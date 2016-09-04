
#######################################
### Dev targets
#######################################
dep-dev:
	sudo apt-get install python3-virtualenv python3-pil.imagetk python3-tk libspeex-dev swig libpulse-dev libspeexdsp-dev
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
	env/bin/pip3 install -r requirements.txt

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
lang-scan:
	pygettext3.5 --output-dir=tuxeatpi/locale/  -k gtt -va -x tuxeatpi/libs/lang.py tuxeatpi/*.py tuxeatpi/*/*.py
	cd tuxeatpi/locale && msgmerge --update --no-fuzzy-matching --backup=off en/LC_MESSAGES/tuxeatpi.po messages.pot
	cd tuxeatpi/locale && msgmerge --update --no-fuzzy-matching --backup=off fr/LC_MESSAGES/tuxeatpi.po messages.pot

lang-gen:
	cd tuxeatpi/locale/fr/LC_MESSAGES/ && msgfmt tuxeatpi.po -o tuxeatpi.mo
	cd tuxeatpi/locale/en/LC_MESSAGES/ && msgfmt tuxeatpi.po -o tuxeatpi.mo

set-locales:
	sudo sed -i 's/# \(en_US.UTF-8 .*\)/\1/g' /etc/locale.gen
	sudo sed -i 's/# \(en_CA.UTF-8 .*\)/\1/g' /etc/locale.gen
	sudo sed -i 's/# \(fr_FR.UTF-8 .*\)/\1/g' /etc/locale.gen
	sudo sed -i 's/# \(fr_CA.UTF-8 .*\)/\1/g' /etc/locale.gen
	sudo locale-gen

hotword-fr:
	# Get acoustic model fr
	mkdir -p pocketsphinx-data/fra-FRA/
	ln -s fra-FRA pocketsphinx-data/fra-CAN
	wget "https://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/French/cmusphinx-fr-ptm-5.2.tar.gz/download" -O pocketsphinx-data/fra-FRA/cmusphinx-fr-ptm-5.2.tar.gz
	cd pocketsphinx-data/fra-FRA/ && tar vxf cmusphinx-fr-ptm-5.2.tar.gz && mv cmusphinx-*-5.2 acoustic-model && rm -f cmusphinx-*-5.2.tar.gz
	wget "https://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/French/fr-small.lm.bin/download" -O pocketsphinx-data/fra-FRA/language-model.lm.bin
	# Get dict
	wget "https://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/French/fr.dict/download" -O pocketsphinx-data/fra-FRA/pronounciation-dictionary.dict

hotword-en:
	# Get acoustic model en
	mkdir -p pocketsphinx-data
	cp -r `python -c "import speech_recognition as sr;import os;print(os.path.dirname(os.path.abspath(sr.__file__)))"`/pocketsphinx-data/en-US pocketsphinx-data/eng-USA

hotword-clean:
	rm -rf pocketsphinx-data

#######################################
### Test targets
#######################################

test-run:
	rm -rf .coverage cover/
	pep8 --max-line-length=100 --exclude='*.pyc' --exclude=tuxeatpi/experimental tuxeatpi
	pylint --rcfile=.pylintrc -r no tuxeatpi
	env/bin/coverage run --include='*/tuxeatpi/*' --omit='*/tuxeatpi/tests/*' `which nosetests` --with-html --with-xunit tuxeatpi tests -svd 
	env/bin/coverage combine
	env/bin/coverage report

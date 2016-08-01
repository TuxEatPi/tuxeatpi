
dep:
	sudo apt-get install python3-virtualenv python3-dev

env-dev:
	virtualenv -p /usr/bin/python3 env
	env/bin/pip3 install -r requirements-dev.txt
	env/bin/pip3 install -r requirements.txt


env:
	virtualenv -p /usr/bin/python3 env
	env/bin/pip3 install RPi.GPIO

doc-update-refs:
	rm -rf doc/source/refs/
	sphinx-apidoc -M -f -e -o doc/source/refs/ tuxeatpi/               

doc-generate:
	cd doc && make html

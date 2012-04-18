# Makefile for lazy devs of deluge plugins

PYTHON = /usr/bin/python

.SILENT:

clean:
	find ./ -name '*~' -exec rm '{}' \; -or -name ".*~" -exec rm '{}' \;
	find ./ -name '*.pyc' -exec rm '{}' \;

dist:
	$(PYTHON) setup.py bdist_egg

dev-install:
	$(PYTHON) setup.py build develop -md ~/.config/deluge/plugins

install: dist
	cp ./dist/NetWatcher-0.1-py2.7.egg ~/.config/deluge/plugins



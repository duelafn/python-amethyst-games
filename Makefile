# SPDX-License-Identifier: LGPL-3.0

PKGNAME = amethyst-games
PKG_VERSION = $(shell python3 -c 'import re; print(re.search("__version__ = \"([\d.]+)\"", open("amethyst_games/__init__.py").read()).group(1))')
PY_FILES = $(shell find tests amethyst_games -type f -name "*.py")

.PHONY: all sdist dist debbuild clean test


check:
	@find amethyst_games example tests setup.py -type f -not -empty -exec perl -nE '($$hit = 1), exit if /SPDX\-License\-Identifier/; END { $$hit or say "$$ARGV: MISSING SPDX-License-Identifier" }' {} \;
	@echo python3 -m flake8 --config=extra/flake8.ini ...
	@python3 -m flake8 --config=extra/flake8.ini example/*.py ${PY_FILES}
	@echo OK

clean:
	rm -rf build dist debbuild .venv2 .venv3 amethyst_games.egg-info
	rm -f MANIFEST
	pyclean .

debbuild: test sdist
	@head -n1 debian/changelog | grep "(${PKG_VERSION}-1)" debian/changelog || (/bin/echo -e "\e[1m\e[91m** debian/changelog requires update **\e[0m" && false)
	rm -rf debbuild
	mkdir -p debbuild
	mv -f dist/${PKGNAME}-${PKG_VERSION}.tar.gz debbuild/${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cd debbuild && tar -xzf ${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cp -r debian debbuild/${PKGNAME}-${PKG_VERSION}/
	cd debbuild/${PKGNAME}-${PKG_VERSION} && dpkg-buildpackage -rfakeroot -uc -us

dist: test debbuild
	@mkdir -p dist/${PKG_VERSION}
	mv -f debbuild/${PKGNAME}_* debbuild/*.deb dist/${PKG_VERSION}/
	rm -rf debbuild

doc:
	epydoc --simple-term --html amethyst_games -o pydoc  --include-log --inheritance grouped

sdist: test
	python3 setup.py sdist

test:
	python3 -m pytest --cov=amethyst_games/ --cov-branch --cov-report=html:_coverage tests example

zip: test
	python3 setup.py sdist --format=zip

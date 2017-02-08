# Author: Dean Serenevy <dean@serenevy.net>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

PKGNAME = amethyst-games
PKG_VERSION = $(shell python -c 'import re; print(re.search("__version__ = \"([\d.]+)\"", open("amethyst/games/__init__.py").read()).group(1))')
PY_FILES = $(shell find amethyst/games -type f -name "*.py")

.PHONY: all sdist dist debbuild clean test


all: test

zip: test
	python3 setup.py sdist --format=zip

sdist: test
	python3 setup.py sdist

dist: test debbuild
	mv -f debbuild/${PKGNAME}_* debbuild/*.deb dist/
	rm -rf debbuild

debbuild: test sdist
	@head -n1 debian/changelog | grep "(${PKG_VERSION}-1)" debian/changelog || (/bin/echo -e "\e[1m\e[91m** debian/changelog requires update **\e[0m" && false)
	rm -rf debbuild
	mkdir -p debbuild
	mv -f dist/${PKGNAME}-${PKG_VERSION}.tar.gz debbuild/${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cd debbuild && tar -xzf ${PKGNAME}_${PKG_VERSION}.orig.tar.gz
	cp -r debian debbuild/${PKGNAME}-${PKG_VERSION}/
	cd debbuild/${PKGNAME}-${PKG_VERSION} && dpkg-buildpackage -rfakeroot -uc -us

test:
	python3 setup.py test >/dev/null
	python2 setup.py test >/dev/null

check:
	@echo python3 -m flake8 --config=extra/flake8.ini ...
	@python3 -m flake8 --config=extra/flake8.ini ${PY_FILES}
	@echo python2 -m flake8 --config=extra/flake8.ini ...
	@python2 -m flake8 --config=extra/flake8.ini ${PY_FILES}
	@echo OK

clean:
	pyclean .
	rm -rf build dist debbuild
	rm -f MANIFEST

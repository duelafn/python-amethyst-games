#!/usr/bin/env python
"""
Game Engine Toolkit
"""
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

import re
import sys

__version__ = re.search(r'(?m)^__version__\s*=\s*"([\d.]+(?:[\-\+~.]\w+)*)"', open('amethyst/games/__init__.py').read()).group(1)

from setuptools import setup, find_packages

import unittest
def my_test_suite():
    return unittest.TestLoader().discover('tests', pattern='test_*.py')

setup(
    name         = 'amethyst-games',
    version      = __version__,
    url          = 'https://github.com/duelafn/python-amethyst-games',
    author       = "Dean Serenevy",
    author_email = 'dean@serenevy.net',
    description  = "Game Engine Toolkit",
    packages     = [ 'amethyst.games', 'amethyst.games.plugin' ],
    requires     = [ 'amethyst.core', 'six' ],
    namespace_packages = [ 'amethyst' ],
    test_suite   = 'setup.my_test_suite',
)

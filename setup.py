#!/usr/bin/env python3
"""
Game Engine Toolkit
"""
# SPDX-License-Identifier: LGPL-3.0
import sys
if sys.version_info < (3,6):
    raise Exception("Python 3.6 required -- this is only " + sys.version)

import io
import os
import re
import setuptools
import unittest

__version__ = re.search(r'(?m)^__version__\s*=\s*"([\d.]+(?:[\-\+~.]\w+)*)"', open('amethyst/games/__init__.py').read()).group(1)

def my_test_suite():
    suite = unittest.TestLoader().discover('tests', pattern='test_*.py')
    if os.environ.get('AMETHEST_TEST_ALL', False):
        suite.addTests(unittest.TestLoader().discover('example', pattern='test_*.py'))
    return suite

with io.open('README.rst', encoding='UTF-8') as fh:
    readme = fh.read()

setuptools.setup(
    name         = 'amethyst-games',
    version      = __version__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        ],
    url          = 'https://github.com/duelafn/python-amethyst-games',
    author       = "Dean Serenevy",
    author_email = 'dean@serenevy.net',
    description  = "Game Engine Toolkit",
    long_description = readme,
    packages     = setuptools.find_packages(exclude=("example",)),
    requires     = [ 'amethyst.core (>=0.8.6)' ],
    python_requires = '>=3.6',
#     install_requires = [ 'setuptools' ],
    namespace_packages = [ 'amethyst' ],
    test_suite   = 'setup.my_test_suite',
)

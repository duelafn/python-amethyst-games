#!/usr/bin/env python
"""
Game Engine Toolkit
"""
# SPDX-License-Identifier: LGPL-3.0

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

setuptools.setup(
    name         = 'amethyst-games',
    version      = __version__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        ],
    url          = 'https://github.com/duelafn/python-amethyst-games',
    author       = "Dean Serenevy",
    author_email = 'dean@serenevy.net',
    description  = "Game Engine Toolkit",
    packages     = setuptools.find_packages(exclude=("example",)),
    requires     = [ 'amethyst.core', 'six' ],
    install_requires = [ 'setuptools' ],
    namespace_packages = [ 'amethyst' ],
    test_suite   = 'setup.my_test_suite',
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0

from __future__ import division, absolute_import, print_function, unicode_literals
import unittest

from amethyst.games import Engine

class MyTest(unittest.TestCase):

    def test_stupid(self):
        engine = Engine()


if __name__ == '__main__':
    unittest.main()

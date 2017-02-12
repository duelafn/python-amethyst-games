#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals
import unittest

from amethyst.games import Engine, EngineRole

class MyTest(unittest.TestCase):

    def test_stupid(self):
        engine = Engine(dict(role="server"))
        self.assertEqual(engine.role, EngineRole.SERVER, "Set engine role")


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0

import unittest

from amethyst.games import Engine, NoticeType
from amethyst.games.util import AmethystGameException

class MyTest(unittest.TestCase):

    def test_stupid(self):
        Engine()

    def test_NoticeType(self):
        with self.assertWarnsRegex(UserWarning, r"Duplicate notice type declaration of 'GRANT'"):
            NoticeType.register(GRANT=NoticeType.GRANT)

        with self.assertRaisesRegex(AmethystGameException, r'already registered'):
            NoticeType.register(GRANT="FOO")


if __name__ == '__main__':
    unittest.main()

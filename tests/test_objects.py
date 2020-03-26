#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0

import collections
import sys
import unittest

from os.path import dirname, abspath
sys.path.insert(1, dirname(dirname(abspath(__file__))))

from amethyst.games.objects.pile import Pile


class TestObjects(unittest.TestCase):

    def test_pile_list(self):
        pile = Pile()
        pile.extend(range(21))

        self.assertEqual(pile.peek(), 20)
        self.assertEqual(pile.pop(),  20)
        self.assertEqual(pile.peek(), 19)

        self.assertEqual(pile.peek(5), [15, 16, 17, 18, 19])
        pile.shuffle()
        self.assertNotEqual(pile.peek(5), [15, 16, 17, 18, 19])

    def test_pile_deque(self):
        pile = Pile(stack=collections.deque(range(21)))

        self.assertEqual(pile.peek(), 20)
        self.assertEqual(pile.pop(),  20)
        self.assertEqual(pile.peek(), 19)

        self.assertEqual(pile.peek(5), [15, 16, 17, 18, 19])
        pile.shuffle()
        self.assertNotEqual(pile.peek(5), [15, 16, 17, 18, 19])


if __name__ == '__main__':
    unittest.main()

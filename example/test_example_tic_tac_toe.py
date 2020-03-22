#!/usr/bin/python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0
import unittest

from example.tic_tac_toe import TicTacToe

class MyTest(unittest.TestCase):

    def test_basic(self):
        game = TicTacToe()


if __name__ == '__main__':
    unittest.main()

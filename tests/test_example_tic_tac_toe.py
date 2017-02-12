#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2017  Dean Serenevy
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program. If not, see <http://www.gnu.org/licenses/>.
from __future__ import division, absolute_import, print_function, unicode_literals
import unittest

from example.tic_tac_toe import TicTacToe

class MyTest(unittest.TestCase):

    def test_basic(self):
        game = TicTacToe(dict(role="server"))
        self.assertEqual(game.role, "server", "Set engine role")


if __name__ == '__main__':
    unittest.main()

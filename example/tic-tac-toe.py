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

import re, sys, os.path
__version__ = '0.0.1'


from amethyst.games import *
from amethyst.core  import *


class TicTacToe(EnginePlugin):

    def start_game(self, game):
        game.next_turn()

    def next_turn(self, game):
        game.turn_start()
        game.grant(game.turn_player_num(), Action("place", data=game.spaces_available()))

    def CHECK_place(self, game, x, y):
        if game.board[y][x] is not None:
            raise InvalidActionException()

    def ACTION_place(self, game, x, y):
        game.board[y][x] = game.turn_player_num()
        game.notify(Action("place", data=dict(x=x, y=y, mark=game.turn_player_num())))
        game.next_turn()


class ToeBoard(Engine):
    board = Attr()
    def __init__(self, width=3, height=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.board is None:
            self.board = [ [None] * width for i in range(height) ]

        self.register(Turns)
        self.register(TicTacToe)

    def spaces_available(self):
        avail = []
        for j, row in enumerate(self.board):
            for i, val in enumerate(row):
                if val is None:
                    avail.append( (i,j) )
        return avail

    def grant(self, players, *actions):
        # Note: send grands in single batch to help UI and AI choose
        if isinstance(players, (int, six.string_types)):
            players = (players,)
        for p in players:
            for a in actions:
                print("{}: {}".format(p, a.to_json()))

    def notify(self, action):
        print("NOTICE: {}".format(action.to_json()))


class AI(Object):
    engine = Attr()


class DumbAI(AI):
    pass


import argparse
def getopts():
    parser = argparse.ArgumentParser(description="""Tool for doing stuff""")

    # http://docs.python.org/2/library/argparse.html
    parser.add_argument('--version', action='version', version='This is %(prog)s version {}'.format(__version__))

    parser.add_argument('first', type=int, help='first weld number to export')
    parser.add_argument('last',  type=int, help='last weld number to export')

    parser.add_argument('--machine', '-m', type=str, help='machine name (defaults to current machine name)')
    parser.add_argument('--output', '-o', type=str, default="welds", help='output directory (default "welds")')

    return parser.parse_args()


def MAIN(argv):
    game = ToeBoard()
    game.start()
    move = input("Move? ").split()
    while len(move) == 2:
        game.call("place", x=move[0], y=move[1])



if __name__ == '__main__':
    MAIN(getopts())

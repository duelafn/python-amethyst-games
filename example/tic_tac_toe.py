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

import copy
import six

from six.moves import input

from amethyst.core  import Object, Attr
from amethyst.games import Engine, EnginePlugin, Action, FILTER_ALL, Filter, Notice
from amethyst.games.plugin import Turns

import argparse
def getopts():
    parser = argparse.ArgumentParser(description="""Tic-Tac-Toe Example Game""")
    parser.add_argument('--ai', type=str, help='AI type')
    parser.add_argument('--size', type=int, default=3, help='Board size')
    return parser.parse_args()


class TicTacToe_Base(EnginePlugin):
    AMETHYST_PLUGIN_COMPAT  = 1.0

    def __init__(self, *args, **qwargs):
        super(TicTacToe_Base,self).__init__(*args, **qwargs)

    def next_turn(self, game):
        game.turn_start()
        game.grant(
            game.turn_player(),
            Action(name="place", data=game.spaces_available()),
        )

    def ACTION_begin(self, game, stash):
        self.next_turn(game)

    def CHECK_place(self, game, stash, x, y):
        return game.board[int(y)][int(x)] is None

    def ACTION_place(self, game, stash, x, y):
        game.board[int(y)][int(x)] = game.turn_player_num()
        game.grant(
            game.turn_player(),
            Action(name="end_turn"),
        )

    def UNDO_place(self, game, stash, x, y):
        game.board[int(y)][int(x)] = None

    def ACTION_end_turn(self, game, stash):
        self.next_turn(game)


class TicTacToe(Engine):
    board   = Attr()
    width   = Attr(default=3)
    height  = Attr(default=3)

    def __init__(self, *args, **kwargs):
        super(TicTacToe,self).__init__(*args, **kwargs)
        if self.board is None:
            self.board = [ [None] * self.width for i in range(self.height) ]
        self.register(Turns())
        self.register(TicTacToe_Base())

    def __str__(self):
        board = []
        for row in self.board:
            board.append("".join( "_" if x is None else str(x) for x in row ))
        return "\n".join(board)

    def spaces_available(self):
        avail = []
        for j, row in enumerate(self.board):
            for i, val in enumerate(row):
                if val is None:
                    avail.append( (i,j) )
        return avail


# Tele-Type Tic-Tac-Toe :)
class TTTTT(Object):
    id = Attr()
    engine = Attr(default=lambda: TicTacToe(client=True))
    player = Attr(int)

    def prompt(self):
        return input("Player {}: ".format(self.player))

    def handle(self):
        cmd = self.prompt().split()
        kwargs = dict()

        filt = None
        if cmd[0] == '?':
            g = set(self.engine.list_grants(self.player))
            G = set(self.server.list_grants(self.player))
            for x in g & G: print(x)
            for x in g - G: print("local  only!", x)
            for x in G - g: print("server only!", x)

        elif cmd[0] == 'e':
            filt = Filter(name="end_turn")

        else:
            filt = Filter(name="place")
            kwargs['x'] = cmd[0]
            kwargs['y'] = cmd[1]

        grants = self.engine.list_grants(self.player, filt) if filt else None
        if grants:
            return grants[0].id, kwargs
        else:
            return None, None

    def on_event(self, game, seq, player, notice):
        if notice.type == Notice.GRANT:
            self.engine.server_grant_notice(notice)
            print("Hey, player {}: GRANT {}".format(player, str(notice.data['actions']['name'])))
        elif notice.type == Notice.EXPIRE:
            self.engine.server_expire_notice(notice)
            print("Hey, player {}: EXPIRE {}".format(player, str(notice.data)))
        elif notice.type == Notice.CALL:
            self.engine.call(notice.name, notice.data)
            print("Hey, player {}: CALL {}".format(player, notice.name))
        else:
            print("Hey, player {}: {}".format(player, str(notice)))


class AI(Object):
    engine = Attr()


class DumbAI(AI):
    pass



def MAIN1(argv):
    game = TicTacToe(dict( width=argv.size, height=argv.size ))
    ui = TTTTT()

    state = game.initialize()
    ui.engine.initialize(state)




def MAIN2(argv):
    ## Build our objects.
    # Here we pretend that multiple players are running independently
    # communicating with an independent server (perhaps all on different
    # machines).
    server = TicTacToe(dict( width=argv.size, height=argv.size ))
    players = [ TTTTT(id=0, player=0), TTTTT(id=1, player=1) ]

    # Server gets initilaized first, then initilization data passed to the clients.
    server.players = [ p.id for p in players ]
    init = server.initialize()
    for p in players:
        p.server = server
        p.engine.initialize(copy.deepcopy(init))
        p.engine.set_state(server.get_state(p.id))

    for player in players:
        server.observe(player.id, player.on_event)

    server.call("begin")

    while True:
        player = server.turn_player()
        id, kwargs = players[player].handle()
        if id is not None:
            server.trigger(player, id, kwargs)
            print(server)


if __name__ == '__main__':
    MAIN2(getopts())

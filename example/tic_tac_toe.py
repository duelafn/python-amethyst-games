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
import random
import six

from six.moves import input

from amethyst.core  import Object, Attr
from amethyst.games import Engine, EnginePlugin, Action, Filter
from amethyst.games.plugin import Turns

# Argument parsing
import argparse
def getopts():
    parser = argparse.ArgumentParser(description="""Tic-Tac-Toe Example Game""")
    parser.add_argument('--size', type=int, default=3, help='Board size')
    return parser.parse_args()


# Tic-Tac-Toe Engine
#
# Primary state object
#
# The Engine base class implements all the flow control, and this class
# implements the core state. Additional methods can be placed here or in plugins.

class TTT_Engine(Engine):
    board   = Attr()
    width   = Attr(default=3)
    height  = Attr(default=3)

    def __init__(self, *args, **kwargs):
        """
        Set up an empty board and load plugins.
        """
        super(TTT_Engine,self).__init__(*args, **kwargs)

        # Empty NxM board
        if self.board is None:
            self.board = [ [None] * self.width for i in range(self.height) ]

        # Most turn-based games will want the Turns plugin
        self.register(Turns())

        # All games need some plugins to implemnt behavior. Some games will
        # always consist of the same plugins, some may load different sets
        # of plugins depending on what game expansions are being played.
        # TicTacToe needs only a single plugin.
        self.register(TicTacToe())

    def spaces_available(self):
        """
        Utility function that computes a list of available places.
        """
        avail = []
        for j, row in enumerate(self.board):
            for i, val in enumerate(row):
                if val is None:
                    avail.append( (i,j) )
        return avail


# Tic-Tac-Toe "Plugin"
#
# Implements actions / game logic
#
# Control methods have the form "_{action}_{stage}_". You can create any
# actions you like and any sequence or combination of actions to move the
# game along. Multiple plugins can be created if it makes organization
# easier.

class TicTacToe(EnginePlugin):
    AMETHYST_PLUGIN_COMPAT = 1  # Plugin API version

    def next_turn(self, game):
        """
        Moving to next turn, clear the undo stack, move to next player's
        turn, and immediately grant new player option to place in any
        available space.
        """
        game.commit()
        game.turn_start()
        game.grant(game.turn_player(), Action(name="place"))

    def _begin_action_(self, game, stash):
        """
        Begin: No setup, just move to first turn.
        """
        self.next_turn(game)

    def _place_check_(self, game, stash, x, y):
        """
        Place check: Verify spot is empty
        """
        return game.board[y][x] is None

    def _place_action_(self, game, stash, x, y):
        """
        Place action: Mark square with player number and grant end of turn action.
        """
        game.board[y][x] = game.turn_player_num()
        game.grant(game.turn_player(), Action(name="end_turn"))

    def _end_turn_action_(self, game, stash):
        """
        End turn action: pretty boring

        In this example, I have a separate "end turn" action (to allow
        undo). If we wanted, we could also have simplified and put this
        .next_turn at the end of the "place" action, then clients would
        just take turns issuing "place".
        """
        self.next_turn(game)


# Tele-Type Tic-Tac-Toe :)
#
# User Interface
#
# Any interface can keep its own engine instance to query game state (as
# known to the player). In this case, we implement the interface
# independent even of the server communication method allowing the same UI
# to be used with a in-process or over-network server (a network would just
# require a layer to relay notices and commands back and forth between
# server and UI).

class TTTTT(Object):
    engine = Attr(default=lambda: TTT_Engine(client=True))
    player = Attr(int)

    def prompt(self):
        """
        Prompt user for input, show board first
        """
        self.print_board()
        return input("Player {}: ".format(self.player))

    def handle(self):
        """
        Currently the player's turn, prompt for a command and return the
        corresponding grant.
        """
        cmd = self.prompt().split()
        kwargs = dict()

        filt = None
        if cmd[0] == '?':# ? - help / list available grants
            print("x y     to place at position x, y")
            print("e       to end turn")
            print("Current grant(s):")
            for x in self.engine.list_grants(self.player):
                print(x)

        elif cmd[0] == 'e':# e - end turn
            filt = Filter(name="end_turn")

        else:# x y - place marker at x, y
            filt = Filter(name="place")
            kwargs['x'] = int(cmd[0])
            kwargs['y'] = int(cmd[1])

        # Search for grants matching the action filter selected. If we find
        # one, call it. Otherwise noop.
        grants = self.engine.list_grants(self.player, filt) if filt else None
        if grants:
            return [ grants[0].id, kwargs ]
        else:
            return None

    def print_board(self):
        """
        Print the current board state to screen.
        """
        for row in self.engine.board:
            print( "".join( "_" if x is None else str(x) for x in row ) )

    def on_event(self, game, seq, player, notice):
        """
        Print notification of every event for illustrative purposes.
        """
        print("Hey, player {}: {}".format(player, str(notice)))


# A simple AI

class DumbAI(TTTTT):
    """
    Dumb AI, places mark on random unoccupied position.
    """
    def handle(self):
        """
        Choose an action from available grants and do it.
        """
        grants = self.engine.list_grants(self.player)

        # This game is simple enough that there is only a single active
        # grant at a time, thus choosing which grant is easy:
        if grants:
           if grants[0].name == 'end_turn':
               return grants[0].id, dict()

           if grants[0].name == 'place':
               # Choosing a placement involves a real choice, be Dumb:
               x, y = random.choice(self.engine.spaces_available())
               return grants[0].id, dict(x=x, y=y)


# Main app - minimal local-only game

def MAIN1(argv):
    """
    Minimal working example. Exposes full game details to all players and
    only useful for non network-based games.
    """
    # Build game and players
    game = TTT_Engine(dict( width=argv.size, height=argv.size, players=[ 0, 1 ] ))
    players = [
        DumbAI(player=0, engine=game),
        TTTTT(player=1, engine=game),
    ]

    # Setup and start the game
    game.initialize()
    game.call("begin")

    while True:
        # Get player action and pass it to the game
        player = players[ game.turn_player() ]
        args   = player.handle()
        if args:
            game.trigger(player.player, *args)



# Main app - client/server example

def MAIN2(argv):
    """
    Simulation of client / server mode. Each player is independent and
    could just as well be running of different machines. Each to/from json
    round-trip indicates where a network transition would take place. See
    amethyst.games.transport for a usable network transport implementation.
    """
    # Build game and players. Players do not get a copy of the server, they
    # each maintain their own engine which will track the state of the
    # server independently.
    server = TTT_Engine(dict( width=argv.size, height=argv.size ))
    players = [
        DumbAI(player=0),
        TTTTT(player=1),
    ]

    # Server gets initilaized first
    server.players = [ p.player for p in players ]
    server.initialize()

    for p in players:
        # Each client requests a standard initialization and personalized
        # state from the server.
        init = server.dumps(server.get_initialization_data())
        player_state = server.dumps(server.get_state(p.player))

        # Initialize player's private engine
        p.engine.initialize(p.engine.loads(init))
        p.engine.set_state(p.engine.loads(player_state))

        # Register to receive event notifications
        server.observe(p.player, p.engine.client_event_listener)
        server.observe(p.player, p.on_event)

    # Start the game!
    server.call("begin")

    while True:
        # Request an action from the current player
        player = players[ server.turn_player() ]
        request = player.engine.dumps(player.handle())

        # If an action was requested, ask the server to execute it (if
        # request succeeds, the server will send notices to clients).
        if request:
            id, kwargs = server.loads(request)
            server.trigger(player.player, id, kwargs)


if __name__ == '__main__':
    MAIN2(getopts())

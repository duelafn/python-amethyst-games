#!/usr/bin/python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0
from __future__ import division, absolute_import, print_function, unicode_literals

import os.path
import random
import sys

from six.moves import input

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from amethyst.core  import Object, Attr
from amethyst.games import Engine, EnginePlugin, Filter
from amethyst.games.plugins import Grants, Turns, Action

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

        # Most turn-based games will want the Grants and Turns plugin
        self.register_plugin(Grants())
        self.register_plugin(Turns())

        # All games need some plugins to implemnt behavior. Some games will
        # always consist of the same plugins, some may load different sets
        # of plugins depending on what game expansions are being played.
        # Some may load a base set of plugins in their constructor and
        # allow the caller to load additional plugins.
        #
        # TicTacToe needs only a single plugin.
        self.register_plugin(TicTacToe())

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
    """
    Simple TicTacToe "Plugin"

    Actions:

      - begin:    start a new game

      - place:    (current player) place a mark on the board

      - end_turn: (current player) end theirt turn after placing, split as a separate action for illustration

    TODO: End of game detection!

    """
    AMETHYST_PLUGIN_COMPAT = 1  # Plugin API version
    AMETHYST_ENGINE_METHODS = ('is_valid_placement')

    def next_turn(self, game):
        """
        Moving to next turn, clear the undo stack, move to next player's
        turn, and immediately grant new player option to place in any
        available space.
        """
        game.commit()
        game.turn_start()
        game.grant(game.turn_player(), Action(name="place"))

    def is_valid_placement(self, game, x, y):
        return game.board[y][x] is None

    def _begin_action_(self, game, stash):
        """
        Begin: No setup, just move to first turn.
        """
        self.next_turn(game)

    def _place_check_(self, game, stash, x, y):
        """
        Place check: Verify spot is empty
        """
        return self.is_valid_placement(game, x, y)

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


# Any interface can keep its own engine instance to query game state (as
# known to the player). Here, we implement the simplest interface possible,
# a client game engine, a place to store the player id, and a couple useful
# methods.

class TTTInterface(Object):
    engine = Attr(default=lambda: TTT_Engine(client=True))
    player = Attr(int)

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


class TTTTT(TTTInterface):
    """
    Tele-Type Tic-Tac-Toe :)

    Human Terminal Interface
    """
    def handle(self):
        """
        Currently the player's turn, prompt for a command and return the
        requested action.
        """
        # Ask player what they want to do
        print("")
        self.print_board()
        cmd = input("Player {}: ".format(self.player)).split()

        # Command parsing, build a filter that select the correct action
        # and set the arguments to pass to that action.
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
            try:
                kwargs['x'] = int(cmd[0])
                kwargs['y'] = int(cmd[1])
                # This is an optional check performed just to make UI
                # nicer. The server does its own validation.
                if not self.engine.is_valid_placement(**kwarge):
                    print("Invalid placement (already occupied)")
                    return None
            except ValueError as err:
                print("Could not parse coordinate")
                return None

        # Our wrapper will interpret a None result as a noop (see below),
        # so to keep this method simple, we just return None if the user
        # asked for help or had a parse error (the wrapper will re-dispatch
        # to us until we give a valid action).
        grants = self.engine.list_grants(self.player, filt) if filt else None
        if grants:
            return [ grants[0].id, kwargs ]
        else:
            return None


class DumbAI(TTTInterface):
    """
    Dumb AI, places mark on random unoccupied position.
    """
    def handle(self):
        """
        Choose an action from available grants and do it.
        """
        grants = self.engine.list_grants(self.player)
        print(grants)
        if not grants:
            exit()

        # This game is simple enough that there is only a single active
        # grant at a time, thus choosing an action is easy:
        if grants:
            if grants[0].name == 'end_turn':
                return grants[0].id, dict()

            if grants[0].name == 'place':
                # Choosing a placement involves a real choice, be Dumb:
                x, y = random.choice(self.engine.spaces_available())
                return grants[0].id, dict(x=x, y=y)


# Main app 1 - minimal local-only game
#
def MAIN1(argv):
    """
    Minimal working example - All players using the same game engine.

    Exposes full game details to all players and only useful for non
    network-based games.
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



# Main app 2 - client/server example
#
def MAIN2(argv):
    """
    Simulation of client / server mode.

    Each player is independent and could just as well be running of
    different machines. Each to/from json round-trip indicates where a
    network transition would take place. See amethyst.games.transport for a
    usable network transport implementation.
    """
    # Build game and players. Players do not get a copy of the server, they
    # each maintain their own engine which will track the state of the
    # game independently.
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
        # state from the server (allowing for per-player secrets).
        init = server.dumps(server.initialization_data)
        player_state = server.dumps(server.get_state(p.player))
        print("INIT:", init)
        print("Player State:", player_state)

        # Initialize player's private engine
        p.engine.initialize(p.engine.loads(init))
        p.engine.set_state(p.engine.loads(player_state))

        # Register to receive event notifications. For a newtwork game, you
        # would need a custom observer which sends the message over the
        # network, here we attach the player dispatcher straight to the
        # server notification stream.
        server.observe(p.player, p.engine.dispatch_event) # Game state observer
        server.observe(p.player, p.on_event)              # Auxiliary observer (prints to terminal)

    # Start the game!
    server.call("begin")

    while True:
        # Request an action from the current player
        player = players[ server.turn_player() ]
        request = player.handle()

        # Pass the request to the server to execute it (if the request
        # succeeds, the server will send notices to clients).
        if request:
            id, kwargs = server.loads(player.engine.dumps(request))
            server.trigger(player.player, id, kwargs)


if __name__ == '__main__':
    MAIN2(getopts())

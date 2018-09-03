# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = 'Turns'.split()

from amethyst.core import Attr

from amethyst.games.plugin import EnginePlugin

class Turns(EnginePlugin):
    AMETHYST_PLUGIN_COMPAT  = 1.0
    AMETHYST_ENGINE_METHODS = "_player _player_num _number _round _start _flag _roundflag _playerflag".split()
    AMETHYST_ENGINE_DEFAULT_METHOD_PREFIX = "turn_"

    current_turn   = Attr(int, default=-1)
    current_round  = Attr(int, default=-1)
    current_player = Attr(int, default=-1)

    def _start(self, engine, player=None, round=None, step=1):
        self.current_turn  += step

        if player is None: player = self.current_turn % len(engine.players)
        if round  is None: round  = int(self.current_turn / len(engine.players))

        self.current_round  = round
        self.current_player = player

    def _player(self, engine):
        return engine.players[self.current_player]

    def _player_num(self, engine):
        return self.current_player

    def _number(self, engine):
        return self.current_turn

    def _round(self, engine):
        return self.current_round

    def _flag(self, engine, turn=None):
        if turn is None: turn = self.current_turn
        return "turn:turn-{}".format(turn)

    def _roundflag(self, engine, round=None):
        if round is None: round = self.current_round
        return "turn:round-{}".format(round)

    def _playerflag(self, engine, player=None):
        if player is None: player = self.current_player
        return "turn:player-{}".format(player)

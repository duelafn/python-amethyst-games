# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
__all__ = 'Turns SwitchbackStartTurns'.split()

from amethyst.core import Attr

from amethyst.games.plugin import EnginePlugin

class Turns(EnginePlugin):
    AMETHYST_PLUGIN_COMPAT  = 1.0
    AMETHYST_ENGINE_METHODS = "_player _player_num _number _round _start _flag _roundflag _playerflag".split()
    AMETHYST_ENGINE_DEFAULT_METHOD_PREFIX = "turn_"

    current_turn   = Attr(int, default=-1)
    current_round  = Attr(default=-1)
    current_player = Attr(int, default=-1)

    def _start(self, engine, player=None, round=None, step=1):
        num_players = len(engine.players)

        if player is None:
            player = self.current_player + step

        if round is None and isinstance(self.current_round, int):
            round = self.current_round
            if self.current_player < 0 or self.current_player + step < 0 or self.current_player + step > num_players:
                round += 1

        self.current_turn  += 1
        if round is not None:
            self.current_round = round
        self.current_player = player % num_players

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


class SwitchbackStartTurns(Turns):
    """
    Turns but with the common "switchback start" mechanism.

    Inserts two rounds called "setup-1" and "setup-2" before starting
    standard numberical rounds 0, 1, ... Player order follows a switchback:

       "setup-1": 0, 1, ... N
       "setup-2": N, N-1, .... 0
       0: 0, 1, ... N
       1: 0, 1, ... N
       ...

    TODO: Add setup_rounds parameter to constructor in case we want more or
    less than 2 setup rounds.
    """
    def _start(self, engine, player=None, round=None, step=1):
        if self.current_round in (-1, 'setup-1', 'setup-2') and player is None and round is None and step == 1:
            if self.current_round == -1:
                round = 'setup-1'
            elif self.current_round == 'setup-1' and self.current_player == len(engine.players) - 1:
                round = 'setup-2'
                step = 0
            elif self.current_round == 'setup-2':
                step = -1
                if self.current_player == 0:
                    round = 0
                    step = 0

        super()._start(engine, player=player, round=round, step=step)

# -*- coding: utf-8 -*-
"""

"""
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
__all__ = 'Turns'.split()

from amethyst.core import Attr
from amethyst.games.engine import EnginePlugin

class Turns(EnginePlugin):
    AMETHYST_PLUGIN_COMPAT  = "1.0"
    AMETHYST_ENGINE_METHODS = "turn_player turn_number turn_round turn_start turn_flag turn_roundflag turn_playerflag".split()

    current_turn   = Attr(int, default=-1)
    current_round  = Attr(int, default=-1)
    current_player = Attr(int, default=-1)

    def turn_start(self, engine, player=None, round=None, step=1):
        self.current_turn  += step

        if player is None: player = (player + step) % len(engine.players)
        if round  is None: round  = int(self.current_turn / len(engine.players))

        self.current_round  = round
        self.current_player = player

    def turn_player(self, engine):
        return engine.players[self.current_player]

    def turn_player_num(self, engine):
        return self.current_player

    def turn_number(self, engine):
        return self.current_turn

    def turn_round(self, engine):
        return self.current_round

    def turn_flag(self, engine, turn=None):
        if turn is None: turn = self.current_turn
        return "turn:turn-{}".format(turn)

    def turn_roundflag(self, engine, round=None):
        if round is None: round = self.current_round
        return "turn:round-{}".format(round)

    def turn_playerflag(self, engine, player=None):
        if player is None: player = self.current_player
        return "turn:player-{}".format(player)

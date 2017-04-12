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
__all__ = 'ObjectStore'.split()

from amethyst.core import Attr
from amethyst.games.engine import EnginePlugin, ADMIN, NOBODY
from amethyst.games.util   import nonce

class ObjectStore(EnginePlugin):
    AMETHYST_PLUGIN_COMPAT  = 1.0
    AMETHYST_ENGINE_METHODS = "stor_get stor_set stor_get_player stor_set_player stor_get_any".split()

    storage = Attr(isa=dict, default=dict)

    def __init__(self, *args, **kwargs):
        super(ObjectStore,self).__init__(*args, **kwargs)
        self.player_storage = dict()

    def stor_get(self, engine, id):
        return self.storage.get(id, None)

    def stor_set(self, engine, obj, id=None):
        if id is None:
            id = self.identify(obj)
        self.storage[id] = obj
        return id

    def stor_get_player(self, engine, player, id):
        if player in self.player_storage:
            return self.player_storage[player].get(id, None)
        return None

    def stor_set_player(self, engine, player, obj, id=None):
        if id is None:
            id = self.identify(obj)
        self.player_storage[player][id] = obj
        return id

    def stor_get_any(self, engine, id):
        if id in self.storage:
            return self.storage[id]
        for stor in self.player_storage.values():
            if id in stor:
                return stor[id]

    def identify(self, obj):
        return nonce()

    def get_state(self, player):
        state = copy.deepcopy(self.dict)
        if player is ADMIN:
            pass # save game: append ALL objects
        elif player is NOBODY:
            return state # kibbitzer, only public knowledge
        elif player in self.player_storage:
            state['player_storage'][player] = copy.deepcopy(self.player_storage[player])

    def set_state(self, state):
        state['player_storage'] = copy.deepcopy(state.pop('player_storage', {}))
        self.set(**state)

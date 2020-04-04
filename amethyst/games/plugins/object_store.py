# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
__all__ = """
ObjectStore
""".split()

import copy

from amethyst.core import Attr

from amethyst.games.filters import Filterable
from amethyst.games.notice  import Notice, NoticeType
from amethyst.games.plugin  import EnginePlugin, event_listener
from amethyst.games.util    import nonce, GAME_MASTER, NOBODY


class ObjectStore(EnginePlugin):
    AMETHYST_PLUGIN_COMPAT  = 1.0
    AMETHYST_ENGINE_METHODS = """
    _get
    _get_player _set_player
    _get_shared _set_shared
    _extend_shared
    """.split()
    AMETHYST_ENGINE_DEFAULT_METHOD_PREFIX = "stor_"

    storage = Attr(isa=dict, default=dict)
    player_storage = Attr(isa=dict, default=dict)


    def _get(self, engine, id):
        if id in self.storage:
            return self.storage[id]
        for stor in self.player_storage.values():
            if id in stor:
                return stor[id]

    def _get_shared(self, engine, id):
        return self.storage.get(id, None)

    def _set_shared(self, engine, id, obj):
        if id is None:
            id = self.identify(obj)
        self.storage[id] = obj
        return id

    def _extend_shared(self, engine, items):
        for x in items:
            if not isinstance(x, Filterable):
                raise Exception("May only bulk-insert Filterable objects into storage")
            self.storage[x.id] = x

    def _get_player(self, engine, player, id):
        if player in self.player_storage:
            return self.player_storage[player].get(id, None)
        return None

    def _set_player(self, engine, player, id, obj):
        if id is None:
            id = self.identify(obj)
        self.player_storage[player][id] = obj
        return id

    def identify(self, obj):
        if isinstance(obj, Filterable):
            return obj.id
        else:
            return nonce()

    def get_state(self, player):
        state = dict(storage=copy.deepcopy(self.storage))
        if player is GAME_MASTER:
            # save game: append ALL objects
            state['player_storage'] = copy.deepcopy(self.player_storage)
        elif player is NOBODY:
            pass # kibbitzer, only public knowledge
        elif player in self.player_storage:
            # Specific player, hide others' data
            state['player_storage'] = { player: copy.deepcopy(self.player_storage[player]) }
        return state

    def set_state(self, state):
        self.set(**state)

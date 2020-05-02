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

NoticeType.register(STORE_SET="::store-set")


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


    def _get(self, game, id):
        if id in self.storage:
            return self.storage[id]
        for stor in self.player_storage.values():
            if id in stor:
                return stor[id]

    def _get_shared(self, game, id):
        return self.storage.get(id, None)

    def _set_shared(self, game, id, obj):
        if id is None:
            id = self.identify(obj)
        self.storage[id] = obj
        game.notify(None, Notice(source=self.id, type=NoticeType.STORE_SET, data=dict(shared=dict(id=obj))))
        return id

    def _extend_shared(self, game, items):
        dd = dict()
        for x in items:
            if not isinstance(x, Filterable):
                raise Exception("May only bulk-insert Filterable objects into storage")
            dd[x.id] = x
        self.storage.update(dd)
        game.notify(None, Notice(source=self.id, type=NoticeType.STORE_SET, data=dict(shared=dd)))

    @event_listener(NoticeType.STORE_SET)
    def on_store_set(self, game, seq, player_num, notice):
        """Process a Notice FROM the server."""
        if game.is_client() and notice.source == self.id:
            if 'shared' in notice.data:
                self.storage.update(notice.data['shared'])
            if 'player' in notice.data:
                for p, data in notice.data['player'].items():
                    if p not in self.player_storage:
                        self.player_storage[p] = dict()
                    self.player_storage[p].update(data)

    def _get_player(self, game, player_num, id):
        if player_num in self.player_storage:
            return self.player_storage[player_num].get(id, None)
        return None

    def _set_player(self, game, player_num, id, obj):
        if id is None:
            id = self.identify(obj)
        self.player_storage[player_num][id] = obj
        game.notify(player_num, Notice(
            source=self.id, type=NoticeType.STORE_SET,
            data=dict(player={ player_num: { id: obj }}),
        ))
        return id

    def identify(self, obj):
        if isinstance(obj, Filterable):
            return obj.id
        else:
            return nonce()

    def get_state(self, player_num):
        state = dict(storage=copy.deepcopy(self.storage))
        if player_num is GAME_MASTER:
            # save game: append ALL objects
            state['player_storage'] = copy.deepcopy(self.player_storage)
        elif player_num is NOBODY:
            pass # kibbitzer, only public knowledge
        elif player_num in self.player_storage:
            # Specific player, hide others' data
            state['player_storage'] = { player_num: copy.deepcopy(self.player_storage[player_num]) }
        return state

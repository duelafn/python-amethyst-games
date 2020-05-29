# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
__all__ = """
ObjectStore
""".split()

import copy

from amethyst.core import Attr

from amethyst.games.filters import FILTER_ALL
from amethyst.games.notice  import Notice, NoticeType
from amethyst.games.plugin  import EnginePlugin, event_listener
from amethyst.games.util    import GAME_MASTER, NOBODY

NoticeType.register(STORE_SET="::store-set")
NoticeType.register(STORE_DEL="::store-del")


class ObjectStore(EnginePlugin):
    """
    Provide a "distributed" item lookup table.

    The object store is a dictionary with a public (shared) part and
    private (per-player) parts. Items added to or removed from the storage
    (via the API) will trigger a notice so that clients can keep their
    storage up to date.

    WARNING: The ObjectStore WILL NOT see changes made directly to your
    stored objects. If data internal to the stored object changes, you will
    need to call the appropriate `stor_set` in order to send the updated
    object to clients.
    """
    AMETHYST_PLUGIN_COMPAT  = 1.0
    AMETHYST_ENGINE_METHODS = """
    _get _del
    _get_player _set_player _del_player _list_player
    _get_shared _set_shared _del_shared _list_shared
    """.split()
    AMETHYST_ENGINE_DEFAULT_METHOD_PREFIX = "stor_"

    # These are not meant to be accessed directly
    _storage = Attr(isa=dict, default=dict)
    _player_storage = Attr(isa=dict, default=dict)


    def _get(self, game, id):
        """
        Get an item by ID from the store. Searches the shared store first, then
        individual player stores (in random order).
        """
        if id in self._storage:
            return self._storage[id]
        for stor in self._player_storage.values():
            if id in stor:
                return stor[id]

    def _del(self, game, *ids):
        """Delete key(s) from shared and all per-player stores. Returns None."""
        for id in ids:
            self._storage.pop(id, None)
            for stor in self._player_storage.values():
                stor.pop(id, None)
        game.notify(None, Notice(source=self.id, type=NoticeType.STORE_DEL, data=dict(all=ids)))

    def _get_shared(self, game, id, dflt=None):
        """Retrieve an item from shared storage"""
        return self._storage.get(id, dflt)

    def _set_shared(self, game, id, obj):
        """Set or update an item in shared storage"""
        self._storage[id] = obj
        game.notify(None, Notice(source=self.id, type=NoticeType.STORE_SET, data=dict(shared={id: obj})))
        return id

    def _del_shared(self, game, *ids):
        """Delete key(s) from shared storage. Returns None."""
        for id in ids:
            self._storage.pop(id, None)
        game.notify(None, Notice(source=self.id, type=NoticeType.STORE_DEL, data=dict(shared=ids)))

    def _list_shared(self, game, filt=FILTER_ALL):
        """Return a list of items in shared storage matching a filter."""
        return [x for x in self._storage.values() if filt.accepts(x)]

    def _get_player(self, game, player_num, id, dflt=None):
        """Retrieve an item from a player storage"""
        if player_num in self._player_storage:
            return self._player_storage[player_num].get(id, dflt)
        return dflt

    def _set_player(self, game, player_num, id, obj):
        """Set or update an item in player storage"""
        self._player_storage[player_num][id] = obj
        game.notify(player_num, Notice(
            source=self.id, type=NoticeType.STORE_SET,
            data=dict(player={ player_num: {id: obj} }),
        ))
        return id

    def _del_player(self, game, player_num, *ids):
        """Delete key(s) from player storage. Returns None."""
        if player_num in self._player_storage:
            for id in ids:
                self._player_storage[player_num].pop(id, None)
        game.notify(player_num, Notice(
            source=self.id, type=NoticeType.STORE_DEL,
            data=dict(player={ player_num: ids }),
        ))

    def _list_player(self, game, player_num, filt=FILTER_ALL):
        """Return a list of items in player storage matching a filter."""
        return [x for x in self._player_storage[player_num].values() if filt.accepts(x)]


    @event_listener(NoticeType.STORE_SET)
    def on_store_set(self, game, seq, player_num, notice):
        """Process a Notice from our upstream."""
        if notice.source == self.id:
            if 'shared' in notice.data:
                for k, v in notice.data['shared'].items():
                    self._set_shared(game, k, v)
            if 'player' in notice.data:
                for p, data in notice.data['player'].items():
                    for k, v in data.items():
                        self._set_player(game, p, k, v)

    @event_listener(NoticeType.STORE_DEL)
    def on_store_del(self, game, seq, player_num, notice):
        """Process a Notice from our upstream."""
        if notice.source == self.id:
            if 'all' in notice.data:
                self._del(game, *notice.data['all'])
            if 'shared' in notice.data:
                self._del_shared(game, *notice.data['shared'])
            if 'player' in notice.data:
                for p, data in notice.data['player'].items():
                    self._del_player(game, p, *data)

    def get_state(self, player_num):
        state = dict(_storage=copy.deepcopy(self._storage))
        if player_num is GAME_MASTER:
            # save game: append ALL objects
            state['_player_storage'] = copy.deepcopy(self._player_storage)
        elif player_num is NOBODY:
            pass # kibbitzer, only public knowledge
        elif player_num in self._player_storage:
            # Specific player, hide others' data
            state['_player_storage'] = { player_num: copy.deepcopy(self._player_storage[player_num]) }
        return state

# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0

__all__ = """
Grant
GrantManager
""".split()

from amethyst.core import Attr

from amethyst_games.notice  import Notice, NoticeType
from amethyst_games.plugin  import EnginePlugin, event_listener
from amethyst_games.util    import tupley
from amethyst_games.filters import Filterable, FILTER_ALL

NoticeType.register(GRANT="::grant")
NoticeType.register(EXPIRE="::expire")


class Grant(Filterable):
    """
    User grant, authorizes a client to call a game action by name

    :ivar str id: Unique identifier

    :ivar str name: Action name to call

    :ivar set(str) flags:

    :ivar dict kwargs: Forced parameters, will override anything requested
        by the client.

    :ivar dict defaults: Default parameters, will supplement anything
        missing from the client call.

    :ivar data:

    :ivar repeatable:

    :ivar list(str) expires: Grant ids which will be expired upon
        successful submission of the action call.
    """

    kwargs = Attr(isa=dict)
    defaults = Attr(isa=dict)
    data = Attr(isa=dict)
    repeatable = Attr(bool)
#     mandatory = Attr(bool)
#     immediate = Attr(bool)
#
#     before = Attr(tupley)
#     after = Attr(tupley)
#     dt_expires = Attr(int)
    expires = Attr(tupley)
#     consumes = Attr(tupley)
#     requires = Attr(tupley)
#     conflicts = Attr(tupley)

    def call(self, **kwargs):
        return Call(id=self.id, name=self.name, kwargs=kwargs)


class Call(Filterable):
    """
    A Call may be used to trigger a grant.

    Often a game will send Grants to clients and receive Calls from
    clients, then trigger the Grant referred to by the Call.
    """
    kwargs = Attr(isa=dict)


class GrantManager(EnginePlugin):
    """
    :ivar grants: Currently active grants. dict: PLAYER_NUM => list(GRANTS)
    """
    AMETHYST_PLUGIN_COMPAT  = 1
    AMETHYST_ENGINE_METHODS = """
    grant
    trigger
    expire
    find_grant
    list_grants
    """.split()

    grants = Attr(isa=dict, default=dict)

    def trigger(self, game, player_num, id, kwargs):
        """
        Player interface to actions

        Actions perform operations on the game state, but actions should
        never be called directly by players. Instead, a player receives
        grants for each action it has been granted permission to trigger.
        When the player wants to perform one of those actions, it triggers
        the action by the grant id, passing along any arguments that the
        action requires.

        Triggered actions will be processed and the action will either
        succeed or fail, causing the grant to be consumed or not (though a
        grant may also be flagged as repeatable in which case it will not
        be consumed even if successful).
        """
        grant = self.find_grant(game, player_num, id)
        if not grant:
            return False

        # Grants can default or force certain kwargs:
        if grant.kwargs or grant.defaults:
            kwargs = { k: v for k, v in kwargs.items() }
        if grant.kwargs:
            kwargs.update(grant.kwargs)
        if grant.defaults:
            for k, v in grant.defaults.items():
                kwargs.setdefault(k, v)

        # Finally try to schedule the action
        if game.schedule(grant.name, kwargs):
            self.expire(game, grant.expires)
            if not grant.repeatable:
                self.expire(game, grant.id)
            return True
        return False

    def _grant(self, game, player_nums, actions):
        for p in tupley(player_nums):
            if p not in self.grants:
                self.grants[p] = dict()
            for a in tupley(actions):
                self.grants[p][a.id] = a
        game.notify(None, Notice(
            source=self.id, type=NoticeType.GRANT,
            data=dict(player_nums=player_nums, actions=actions),
        ))

    def grant(self, game, player_nums, actions):
        """Process a grant Notice AS the server."""
        if game.is_server():
            self._grant(game, player_nums, actions)
        return self
    @event_listener(NoticeType.GRANT)
    def on_grant(self, game, seq, player_num, notice):
        """Process a grant Notice FROM the server."""
        if game.is_client() and notice.source == self.id:
            self._grant(game, notice.data.get('player_nums'), notice.data.get('actions'))

    def _expire(self, game, filters):
        if not filters:
            return
        game.notify(None, Notice(
            source=self.id, type=NoticeType.EXPIRE,
            data={ 'filters': filters },
        ))
        for filt in filters:
            # Optimization for a common case
            if filt is FILTER_ALL:
                self.grants = dict()
                return
            elif isinstance(filt, str):
                for g in self.grants.values():
                    g.pop(filt, None)
            else:
                for p in self.grants:
                    self.grants[p] = [ a for a in self.grants[p] if not filt.accepts(a) ]

    def expire(self, game, filters=FILTER_ALL):
        if filters is not None:
            self._expire(game, tupley(filters))
        return self
    @event_listener(NoticeType.EXPIRE)
    def on_expire(self, game, seq, player_num, notice):
        """Process an expire Notice from the server."""
        if game.is_client() and notice.source == self.id:
            self._expire(game, notice.data.get('filters'))

    def find_grant(self, game, player_num, id):
        """
        Find a player grant by id and returns it, else returns `None`.
        """
        if player_num in self.grants:
            if id in self.grants[player_num]:
                a = self.grants[player_num][id]
                if isinstance(a, Grant):
                    return a
        return None

    def list_grants(self, game, player_num, filt=FILTER_ALL):
        """
        Return a tuple of player grants matching the requested filter (default all grants).
        """
        if player_num not in self.grants:
            return ()

        if filt is FILTER_ALL:
            return tuple(self.grants[player_num].values())
        else:
            return tuple(a for a in self.grants[player_num].values() if filt.accepts(a))

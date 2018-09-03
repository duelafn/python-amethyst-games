# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
from __future__ import division, absolute_import, print_function, unicode_literals

__all__ = """
Action
Grants
""".split()

import six

from amethyst.core import Attr

from amethyst.games.notice  import Notice, NoticeType
from amethyst.games.plugin  import EnginePlugin, event_listener
from amethyst.games.util    import tupley
from amethyst.games.filters import Filterable, FILTER_ALL

NoticeType.register(GRANT=":grant")
NoticeType.register(EXPIRE=":expire")

# class Achievement(Filterable):
#     @classmethod
#     def from_action(cls, action):
#         init = dict(id=action.id)
#         if action.name: init['name'] = action.name
#         if action.flags: init['flags'] = set(action.flags)
#         return cls(init)

class Action(Filterable):
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


class Grants(EnginePlugin):
    """
    :ivar grants: Currently active grants. dict: PLAYER_ID => list(GRANTS)
    """
    AMETHYST_PLUGIN_COMPAT  = 1
    AMETHYST_ENGINE_METHODS = """
    expire
    find_grant
    grant
    list_grants
    trigger
    """.split()

    grants = Attr(isa=dict, default=dict)

    def trigger(self, game, player, id, kwargs):
        """
        Player interface to actions

        call() may be the mover and shaker of the engine, but it lives in a
        gated community, and trigger() holds the keys.

        Actions perform operations on the game state, but actions should
        never be called directly by players. Instead, a player receives
        grants for each action is has been granted permission to trigger.
        When the player wants to perform one of those actions, it triggers
        the action by the grant id, passing along any arguments that the
        action requires.

        Triggered actions will be processed and the action will either
        succeed or fail, causing the grant to be consumed or not (though a
        grant may also be flagged as repeatable in which case it will not
        be consumed even if successful).
        """

        a = self.find_grant(game, player, id)
        if not a: return False

        # Actions can default or force certain kwargs:
        if a.kwargs or a.defaults:
            kwargs = { k: v for k, v in kwargs.items() }
        if a.kwargs:
            kwargs.update(a.kwargs)
        if a.defaults:
            for k, v in six.iteritems(a.defaults):
                kwargs.setdefault(k, v)

        # Finally call the action
        ok = game.call(a.name, kwargs)

        if ok:
            self.expire(game, a.expires)
            if not a.repeatable:
                self.expire(game, a.id)

    def _grant(self, game, players, actions):
        for p in tupley(players):
#             print(id(game), "grant notify", p, actions)
            game.notify(p, Notice(type=NoticeType.GRANT, data=dict(players=p, actions=actions)) )
            if p not in self.grants:
                self.grants[p] = dict()
            for a in tupley(actions):
                self.grants[p][a.id] = a

    def grant(self, game, players, actions):
#         if game.is_server():
#             print(id(game), "SERVER: grant", str(actions))
        self._grant(game, players, actions)
        return self

    @event_listener(NoticeType.GRANT)
    def server_grant_notice(self, game, seq, player, notice):
        """Process a grant Notice from the server."""
#         print(id(game), "CLIENT: grant notice", str(notice))
        if game.is_client():
            self._grant(game, notice.data.get('players'), notice.data.get('actions'))

    def _expire(self, game, filters=FILTER_ALL):
        if not filters:
            return
        game.notify(game.players, Notice(type=NoticeType.EXPIRE, data=filters))
        for filt in tupley(filters):
            # Optimization for a common case
            if filt is FILTER_ALL:
                self.grants = dict()
                return
            elif isinstance(filt, six.text_type):
                for g in self.grants.values():
                    g.pop(filt, None)
            else:
                for p in self.grants:
                    self.grants[p] = [ a for a in self.grants[p] if not filt.accepts(a) ]

    def expire(self, game, filters=FILTER_ALL):
#         if game.is_server():
        self._expire(game, filters)
        return self

    @event_listener(NoticeType.EXPIRE)
    def server_expire_notice(self, game, notice):
        """Process an expire Notice from the server."""
        if game.is_client():
            self._expire(game, notice.data)

    def find_grant(self, game, player, id):
        """
        Find a player grant by id and returns it, else returns `None`.
        """
        if player in self.grants:
            if id in self.grants[player]:
                a = self.grants[player][id]
                if isinstance(a, Action):
                    return a
        return None

    def list_grants(self, game, player, filt=FILTER_ALL):
        """
        Return a tuple of player grants matching the requested filter (default all grants).
        """
#         print(id(game), "list_grants", str(self.grants))
        if player not in self.grants:
            return ()

        if filt is FILTER_ALL:
            return tuple(self.grants[player].values())
        else:
            return tuple(a for a in self.grants[player].values() if filt.accepts(a))

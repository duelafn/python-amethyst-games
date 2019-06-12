# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = 'Engine'.split()

import collections
import copy
import json
import random
import six
import six.moves.queue as queue
import threading

from amethyst.core import Object, Attr, cached_property

from .notice import Notice, NoticeType
from .util import UnknownActionException, PluginCompatibilityException, NotificationSequenceException
from .util import tupley

NoticeType.register(CALL=":call")
NoticeType.register(INIT=":init")

ENGINE_CALL_ORDER = "before action after".split()
ENGINE_CALL_TYPES = ENGINE_CALL_ORDER + "check init notify undo".split()

class Engine(Object):
    """Engine

    :ivar plugins: list of plugin `Object`s.

    :ivar players: list of players. String or integer identifiers.

    :ivar undoable: Number of undoable actions.
    """
    players  = Attr(isa=list, default=list)
    plugins  = Attr(isa=list, default=list)
    undoable = Attr(isa=int,  default=0)
    # Private attributes:
    #   _client_mode:  bool: True when running in client mode
    #   _client_seq:    int: client event sequence number
    #   initialization_data: dict: cached initialization data
    #   actions:       dict: NAME => CALLBACK
    #   journal:       list: tuple(action, kwargs)
    #   notified:      dict: PLAYER => [ [ COUNTER, CALLBACK ], ... ]
    #   player          str: if non Null, may be used as default player id in some methods
    #   plugin_names:   set: cached list of plugin names as strings (for dependency checking)

    def __init__(self, *args, **kwargs):
        client = kwargs.pop("client", False)
        super(Engine,self).__init__(*args, **kwargs)

        self._client_mode = client
        self._client_seq = 0
        self._event_dispatch = { NoticeType.CALL: [ self.call_event_listener ] }
        self.actions = dict()
        self.journal = [ ]
        self.notified = dict()
        self.player = kwargs.pop("player", None)
        self.plugin_names = set()

        self._queue = queue.Queue()

        for plugin in self.plugins:
            self.register_plugin(plugin)

    def process_queue(self, block=False, timeout=0.1):
        try:
            while True:
                typ, args, kwargs = self._queue.get(block, timeout)
                print((typ, args))
                if typ == 'call':
                    self.call_immediate(*args, **kwargs)
                elif typ == 'notify':
                    self.notify_immediate(*args, **kwargs)
                elif typ == 'exit':
                    return False
                else:
                    raise Exception("Bad queue item: {}".format(typ))
        except queue.Empty:
            print("queue.Empty")
            pass
        return True

    def run(self):
        while self.process_queue(True, None):
            pass

    def shutdown(self):
        self._queue.put(('exit', None, None))
        return self

    def schedule(self, *args, **kwargs):
        self._queue.put(('call', args, kwargs))
        return self

    def notify(self, *args, **kwargs):
        self._queue.put(('notify', args, kwargs))
        return self

    def is_client(self):
        """True when running in client mode"""
        return self._client_mode

    def is_server(self):
        """True when running in server mode"""
        return not self._client_mode

    def make_mutable(self):
        """Marks engine and all plugins mutable"""
        super(Engine,self).amethyst_make_mutable()
        for p in self.plugins:
            p.make_mutable()

    def make_immutable(self):
        """Marks engine and all plugins immutable"""
        super(Engine,self).amethyst_make_immutable()
        for p in self.plugins:
            p.make_immutable()

    def call_immediate(self, name, kwargs=None):
        """Call an action by name.

        Main mover and shaker of the engine. When an action is called, we
        set the immutable flag and execute the `_{action}_check_` method in
        each registered plugin in registration order. If any return False,
        the action is aborted and False is returned.

        - check    : [immutable] return False to cancel the action
        - init     : [immutable] changes to the stash will be saved in the journal (generate random numbers here)

        - before
        - action   : action phase
        - after
        - keep     : called after after only if no callbacks raised an exception
        - undo     : called after after only if any callback raises an exception
        - notify   :

        .. note:: Technically, the immutability flag is only advisory, but
        since there is no unrolling mechanism for partially completed
        _check_, it is a bad idea for plugins to attempt to bypass immutability.

        After the _init_ phase, the immutable flag is unset, a checkpoint is
        made and the action is accepted / added to the journal. Then, for
        each of before, action, and after phases the `_{action}_{phase}_`
        method is executed for each registered plugin in registration
        order.

        `_{action}_{phase}_` methods should have the signature:

            def _{action}_{phase}_(self, engine, stash, **kwargs):

        * `self`: the engine plugin itself
        * `engine`: this engine object
        * `stash`: a dictionary to save state for this particular action event
        * `kwargs`: any arguments required for the action

        After the action executes, a copy of the action arguments will be
        passed to the `_{action}_notify_` method once for each player.
        The method may return a new or modified dict which will be sent as
        a notification to the player. Uses for this are to censor secret
        information or to include additional game state. The notify method
        has a different signature, it takes a player id and kwargs are
        passed as a dictionary reference, a copy of the original arguments
        which may be returned modified:

            def _{action}_notify_(self, engine, stash, player, kwargs):
                return kwargs  # customized for player

        .. todo:: 1.0: Automatic roll-back if an exception is raised in any
        of the action handlers.

        :raises UnknownActionException: If action does not exist.

        """
        if kwargs is None:
            kwargs=dict()
        actions = self.actions.get(name)
        if actions is None:
            raise UnknownActionException("No such action '{}'".format(name))

        stash = dict()
        immutable = False
        try:
            if "check" in actions:
                if not immutable:
                    self.make_immutable()
                    immutable = True
                for cb in actions["check"]:
                    if not cb(self, stash, **kwargs):
                        return False
            if "init" in actions:
                if not immutable:
                    self.make_immutable()
                    immutable = True
                for cb in actions["init"]:
                    cb(self, stash, **kwargs)
        finally:
            if immutable:
                self.make_mutable()

        # Save game state for UNDO and roll-back
        self.journal.append( (name, kwargs, stash) )
        self.undoable += 1

        # Execute the action, all the fun happens here
        for stage in ENGINE_CALL_ORDER:
            if stage in actions:
                for cb in actions[stage]:
                    cb(self, stash, **kwargs)

        # If anyone wants to be notified, send them notification information.
        for player in self.notified:
            p_kwargs = copy.deepcopy(kwargs)
            if "notify" in actions:
                for cb in actions["notify"]:
                    if p_kwargs is not None:
                        p_kwargs = cb(self, stash, player, p_kwargs)
            if p_kwargs is not None:
                self.notify(player, Notice(name=name, type=NoticeType.CALL, data=p_kwargs))

        if actions.get('autocommit', False):
            self.commit()
        return True

    def observe(self, player, cb):
        """
        Register a callback to receive all notifications for the given player.

        Callback should have the following signature:

            def callback(engine, seq, player, notice):

        * `engine`: this engine object
        * `seq`: notification sequence number
        * `player`: player id
        * `notice`: Notice object

        The sequence number is a per-callback, sequentially increasing
        notification id. The first notification an observer will receive
        will have sequence number 1 and the sequence will increase by
        exactly 1 for each notification sent to that callback. A client on
        the other end of that callback should track the sequence state and
        request a the full game state if an out-of-sequence id is received.
        """
        if not player in self.notified:
            self.notified[player] = []
        self.notified[player].append([ 0, cb ])

    def unobserve(self, player, cb):
        """
        Unregister a callback to receive all notifications for the given player.

        Callback must be the identical function or method passed to the
        `observe` method.
        """
        if player in self.notified:
            self.notified[player] = [ pair for pair in self.notified[player] if pair[1] is not cb ]

    def notify_immediate(self, player, notice):
        """Send a notice to one or more players"""
#         print(id(self), "notify", player, notice)
        for p in tupley(player):
            if p in self.notified:
                for pair in self.notified[p]:
                    pair[0] += 1
                    pair[1](self, pair[0], p, notice)

    def commit(self, n=0):
        if n < self.undoable:
            self.undoable = n

    def register_plugin(self, plugin):
        """
        Register a plugin instance. Merges engine methods and plugin actions.
        """
        name = plugin.__class__.__name__
        self.plugins.append(plugin)
        self.plugin_names.add(name)

        for dep in tupley(plugin.AMETHYST_ENGINE_DEPENDS):
            if dep not in self.plugin_names:
                raise PluginCompatibilityException("Plugin {} requires plugin {}".format(name, dep))

        for attr in tupley(plugin.AMETHYST_ENGINE_METHODS):
            meth = attr[1:] if attr.startswith("_") else attr
            if plugin.amethyst_method_prefix:
                meth = "{}{}".format(plugin.amethyst_method_prefix, meth)
            if plugin.amethyst_method_suffix:
                meth = "{}{}".format(meth, plugin.amethyst_method_suffix)

            if hasattr(self, meth):
                raise PluginCompatibilityException("Engine already has a method '{}' (attempted override by {})".format(meth, name))
            self._register_method(meth, getattr(plugin, attr))

        for attr in dir(plugin):
            if attr.startswith("_") and attr.endswith("_"):
                for prefix in ENGINE_CALL_TYPES:
                    if attr.endswith("_{}_".format(prefix)) and len(attr) > 3 + len(prefix):
                        action = attr[1:-(2+len(prefix)):]
                        if action not in self.actions:
                            self.actions[action] = dict()
                        if prefix not in self.actions[action]:
                            self.actions[action][prefix] = list()

                        if prefix in ENGINE_CALL_ORDER and not hasattr(plugin, "_{}_undo_".format(action)):
                            self.actions[action]['autocommit'] = True

                        self.actions[action][prefix].append(getattr(plugin, attr))

    def _register_method(self, name, callback):
        """Method exists just to make closure work"""
        setattr(
            self, name,
            lambda *args, **kwargs: callback(self, *args, **kwargs)
        )


    def initialize(self, attrs=None):
        self.initialize_early(attrs)

        if attrs is not None:
            plugin_init = attrs.pop("plugin_init", [])
            self.load_data(attrs, verifyclass=False)
            for idx, p in enumerate(self.plugins):
                p.initialize_early(self, plugin_init[idx] if idx < len(plugin_init) else None)
            for idx, p in enumerate(self.plugins):
                p.initialize(self, plugin_init[idx] if idx < len(plugin_init) else None)
            for idx, p in reversed(list(enumerate(self.plugins))):
                p.initialize_late(self, plugin_init[idx] if idx < len(plugin_init) else None)

        else:
            for p in self.plugins:
                p.initialize_early(self)
            for p in self.plugins:
                p.initialize(self)
            for p in reversed(self.plugins):
                p.initialize_late(self)

        self.initialize_late(attrs)

        # (re-)build initial state
        del self.initialization_data
        return self.initialization_data

    def initialize_early(self, attrs=None):
        pass

    def initialize_late(self, attrs=None):
        pass

    @cached_property
    def initialization_data(self):
        data = copy.deepcopy(self.dict)
        data["plugin_init"] = [ p.initialization_data for p in self.plugins ]
        return data

    def get_state(self, player):
        d = copy.deepcopy(self.dict)
        d['plugin_state'] = [ p.get_state(player) for p in tupley(d.pop('plugins', [])) ]
        return d

    def set_state(self, state):
        plugin_state = state.pop("plugin_state", [])
        self.set(**state)
        for idx, p in enumerate(self.plugins):
            try:
                p.set_state(plugin_state[idx])
            except IndexError:
                pass

    def set_random_player(self, player, num_players):
        if len(self.players) > num_players:
            raise Exception("Player list exceeds max players ({})".format(num_players))
        if len(self.players) < num_players:
            self.players.extend([None]*(num_players-len(self.players)))
        idx = random.choice(tuple(i for i in range(num_players) if self.players[i] is None))
        self.players[idx] = player
        return idx

    def dumps(self, data):
        return json.dumps(data, default=self.JSONEncoder)

    def loads(self, data):
        return json.loads(data, object_hook=self.JSONObjectHook)

    def call_event_listener(self, game, seq, player, notice):
        self.schedule(notice.name, notice.data)

    def register_event_listener(self, type, listener):
        if type not in self._event_dispatch:
            self._event_dispatch[type] = []
        self._event_dispatch[type].append(listener)
#         print(id(self), "register listener", self._event_dispatch.keys())

    def dispatch_event(self, game, seq, player, notice):
        """
        Responds to standard engine-related notifications. Client engines
        should attach this method via `.observe()` in order to keep the
        local engine up to date.

        :raises NotificationSequenceException: If receive a non-consecutive
        sequence number. In this case, client should re-syncronize via
        get_state/set_state.
        """
        self._client_seq += 1
        if seq != self._client_seq:
            raise NotificationSequenceException("got {} expected {}".format(seq, self._client_seq))

#         print(id(self), "dispatch", self._event_dispatch.keys())
        if notice.type in self._event_dispatch:
            for cb in self._event_dispatch[notice.type]:
                cb(game, seq, player, notice)

        if None in self._event_dispatch:
            for cb in self._event_dispatch[None]:
                cb(game, seq, player, notice)

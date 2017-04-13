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

__all__ = '''
Engine EnginePlugin

AmethystGameException
  PluginCompatibilityException
  UnknownActionException

ADMIN NOBODY
'''.split()

import copy
import json
import six

from amethyst.core import Object, Attr

from .action import Action, Filterable, ClsFilterAll, FILTER_ALL
from .notice import Notice
from .util   import tupley

ADMIN = {}
NOBODY = None

class AmethystGameException(Exception): pass
class PluginCompatibilityException(AmethystGameException): pass
class UnknownActionException(AmethystGameException): pass

class EnginePlugin(Object):
    """EnginePlugin

    @cvar AMETHYST_ENGINE_DEPENDS: Iterable collection of plugin class
        names (as strings) which this plugin delends on. An exception will
        be thrown if any dependencies are not available when the plugin is
        registered.
    @type AMETHYST_ENGINE_DEPENDS: Any iterable of str

    @cvar AMETHYST_ENGINE_METHODS: Iterable collection of methods to be
        added to the engine object which will be handled by this plugin. It
        is an error for multiple plugins to define the same method, so be
        considerate and try to prefix your method names to avoid
        collisions.
    @type AMETHYST_ENGINE_METHODS: Any iterable of str

    @cvar AMETHYST_PLUGIN_COMPAT: Plugin version number as a float or int.
        Plugin version compatibility between instances is ensured via the
        integer portion of this value. (See `compat`)
    @type AMETHYST_PLUGIN_COMPAT: float or int

    @ivar compat: Version number of instance. When plugin data is
        deserialized, this value is compared against the class variable
        `AMETHYST_PLUGIN_COMPAT`. If they do not have the same integer
        value, an exception will be thrown.
    """
    AMETHYST_ENGINE_DEPENDS = ()
    AMETHYST_ENGINE_METHODS = ()
    # Compatibility: class attr hard-coded, instance attr used when passing
    # constructed objects over the wire. Allows server to verify that the
    # server plugin version is compatible with the client plugin version.
    AMETHYST_PLUGIN_COMPAT  = None
    compat = Attr(isa=float)

    def __init__(self, *args, **kwargs):
        super(EnginePlugin,self).__init__(*args, **kwargs)
        if self.compat is None:
            self.compat = self.AMETHYST_PLUGIN_COMPAT
        if self.AMETHYST_PLUGIN_COMPAT is None:
            raise PluginCompatibilityException("Plugin {} does not define an api version".format(self.__class__.__name__))
        if int(self.compat) != int(self.AMETHYST_PLUGIN_COMPAT):
            raise PluginCompatibilityException("Plugin {} imported incompatible serialized data: Loaded {} data, this is version {}".format(self.__class__.__name__, self.compat, self.AMETHYST_PLUGIN_COMPAT))

    def initialize(self, *args):
        if len(args) > 0:
            if args[0] is None: return
            self.load_data(args[0], verifyclass=False)
        else:
            return dict()

    def get_state(self, player):
        return copy.deepcopy(self.dict)

    def set_state(self, state):
        self.set(**state)




ENGINE_CALL_ORDER = "BEFORE ACTION AFTER".split()
ENGINE_CALL_TYPES = ENGINE_CALL_ORDER + "CENSOR CHECK UNDO".split()

class Engine(Object):
    """Engine

    @ivar plugins: list of plugin `Object`s.

    @ivar players: list of players. String or integer identifiers.

    @ivar grants: Currently active grants. dict: PLAYER_ID => list(GRANTS)

    @ivar undoable: Number of undoable actions.
    """
    plugins  = Attr(builder=set)
    players  = Attr(isa=list, default=list)
    grants   = Attr(isa=dict, default=dict)
    undoable = Attr(isa=int,  default=0)
    # Private attributes:
    #   notified:      dict: PLAYER => [ [ COUNTER, CALLBACK ], ... ]
    #   actions:       dict: NAME => CALLBACK
    #   journal:       list: tuple(action, kwargs)
    #   plugin_pkgs:   list: plugin search path (packages containing plugins)
    #   plugin_names:   set: cached list of plugin names as strings (for dependency checking)
    #   _client_mode:  bool: True when running in client mode

    def __init__(self, *args, **kwargs):
        self._client_mode = kwargs.pop("client", False)
        self.actions = dict()
        self.journal = [ ]
        self.notified = dict()
        self.plugin_names = set()
        self.plugin_pkgs = [ ]

        super(Engine,self).__init__(*args, **kwargs)
        for plugin in self.plugins:
            self.register(plugin)




    def is_client(self):
        """True when running in client mode"""
        return self._client_mode

    def is_server(self):
        """True when running in server mode"""
        return not self._client_mode


    def make_mutable(self):
        """Marks engine and all plugins mutable"""
        super(Engine,self).make_mutable()
        for p in self.plugins:
            p.make_mutable()

    def make_immutable(self):
        """Marks engine and all plugins immutable"""
        super(Engine,self).make_immutable()
        for p in self.plugins:
            p.make_immutable()

    def call(self, name, kwargs=None):
        """Call an action by name.

        Main mover and shaker of the engine. When an action is called, we
        set the immutable flag and execute the `CHECK_{action}` method in
        each registered plugin in registration order. If any return False,
        the action is aborted and False is returned.

        @note: Technically, the immutability flag is only advisory, but
        since there is no unrolling mechanism for partially completed
        CHECK, it is a bad idea for plugins to attempt to bypass immutability.

        After the CHECK phase, the immutable flag is unset, a checkpoint is
        made and the action is accepted / added to the journal. Then, for
        each of BEFORE, ACTION, and AFTER phases the `{phase}_{action}`
        method is executed for each registered plugin in registration
        order.

        `{phase}_{action}` methods should have a signature:

            def PHASE_action(self, engine, stash, **kwargs):

        * `self`: the engine plugin itself
        * `engine`: this engine object
        * `stash`: a dictionary to save state for this particular action event
        * `kwargs`: any arguments required for the action

        After the action executes, a copy of the action arguments will be
        passed to the `CENSOR_{action}` method once for each player. The
        CENSOR may remove any information in the action arguments which
        should not be shared with the indicated player. The CENSOR method
        has a different signature, it takes a player id and kwargs are
        passed as a dictionary reference:

            def CENSOR_action(self, engine, stash, player, kwargs):


        @todo 1.0: Automatic roll-back if an exception is raised in any of
        the action handlers.

        @raise UnknownActionException: If action does not exist.

        """
        if kwargs is None:
            kwargs=dict()
        actions = self.actions.get(name)
        if actions is None:
            raise UnknownActionException("No such action '{}'".format(name))

        stash = dict()
        if "CHECK" in actions:
            try:
                self.make_immutable()
                for cb in actions["CHECK"]:
                    if not cb(self, stash, **kwargs):
                        return False
            finally:
                self.make_mutable()

        # Save game state for UNDO and roll-back
        self.journal.append( (name, kwargs, stash, { k: copy.copy(v) for k, v in six.iteritems(self.grants) }) )

        # Execute the action, all the fun happens here
        for stage in ENGINE_CALL_ORDER:
            if stage in actions:
                for cb in actions[stage]:
                    cb(self, stash, **kwargs)

        # If anyone wants to be notified of events, send them CENSOR-ed information.
        for player in self.notified:
            p_kwargs = copy.deepcopy(kwargs)
            if "CENSOR" in actions:
                for cb in actions["CENSOR"]:
                    cb(self, stash, player, p_kwargs)
            self.notify(player, Notice(name=name, type=Notice.CALL, data=p_kwargs))

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

        The sequence number is a private, increasing notification sequence
        number. The first notification an observer will receive will have
        sequence number 0 and the sequence will increase by exactly 1 for
        each notification sent. A client should track its sequence state
        and request a reload of the complete game state if a non-sequential
        sequence number is ever received.
        """
        if not player in self.notified:
            self.notified[player] = []
        self.notified[player].append([ -1, cb ])

    def unobserve(self, player, cb):
        """
        Unregister a callback to receive all notifications for the given player.

        Callback must be the identical function or method passed to the
        `observe` method.
        """
        if player in self.notified:
            self.notified[player] = [ pair for pair in self.notified[player] if pair[1] is not cb ]


    def notify(self, player, notice):
        """Send a notice to one or more players"""
        for p in tupley(player):
            if p in self.notified:
                for pair in self.notified[p]:
                    pair[0] += 1
                    pair[1](self, pair[0], p, notice)

    def commit(self, n=0):
        if n < self.undoable:
            self.undoable = n

    def insert_plugin_package(self, *pkgs):
        """
        Prepends one or more packages to the list searched for named plugins.
        """
        self.plugin_pkgs[:0] = pkgs

    def isa(self, cls, *args, **kwargs):
        """
        Register a plugin by name. Searches registered plugin packages and
        initializes an instance from the passed arguments.

        @todo: is this needed / wanted? Does it work?
        """
        if isinstance(cls, six.string_types):
            for pkg in self.plugin_pkgs:
                if hasattr(pkg, cls):
                    cls = getattr(pkg, cls)
                    break
        self.register(cls(*args, **kwargs))

    def register(self, plugin):
        """
        Register a plugin instance. Merges engine methods and plugin actions.
        """
        name = plugin.__class__.__name__
        self.plugins.add(plugin)
        self.plugin_names.add(name)

        for dep in tupley(plugin.AMETHYST_ENGINE_DEPENDS):
            if dep not in self.plugin_names:
                raise PluginCompatibilityException("Plugin {} requires plugin {}".format(name, dep))

        for attr in tupley(plugin.AMETHYST_ENGINE_METHODS):
            if hasattr(self, attr):
                raise PluginCompatibilityException("Engine already has a method '{}' (attempted override by {})".format(attr, name))
            self._register_method(attr, plugin)

        for attr in dir(plugin):
            for prefix in ENGINE_CALL_TYPES:
                if attr.startswith(prefix + "_"):
                    action = attr[(1+len(prefix)):]
                    if action not in self.actions:
                        self.actions[action] = dict()
                    if prefix not in self.actions[action]:
                        self.actions[action][prefix] = list()

                    if prefix in ENGINE_CALL_ORDER and not hasattr(plugin, "UNDO_{}".format(action)):
                        self.actions[action]['autocommit'] = True

                    self.actions[action][prefix].append(getattr(plugin, attr))

    def _register_method(self, name, plugin):
        """Method exists just to make closure work"""
        setattr(
            self, name,
            lambda *args, **kwargs: getattr(plugin, name)(self, *args, **kwargs)
        )


    def initialize(self, *args):
        if len(args) > 0:
            stuff = args[0]
            if stuff is None: return
            plugin_init = stuff.pop("plugin_init", [])
            self.load_data(stuff, verifyclass=False)
            for idx, p in enumerate(self.plugins):
                try:
                    init = plugin_init[idx]
                except IndexError:
                    init = None
                p.initialize(init)
        else:
            return dict(
                plugin_init=[ p.initialize() for p in self.plugins ],
            )

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

#     def dumps(self, data):
#         return json.dumps(data, default=self.JSONEncoder)
#
#     def loads(self, data):
#         return json.loads(data, object_hook=self.JSONObjectHook)

    def _grant(self, players, actions):
        for p in tupley(players):
            self.notify( p, Notice(type=Notice.GRANT, data=dict(players=p, actions=actions)) )
            if p not in self.grants:
                self.grants[p] = dict()
            for a in tupley(actions):
                self.grants[p][a.id] = a

    def grant(self, players, actions):
        if not self._client_mode:
            self._grant(players, actions)
        return self

    def server_grant_notice(self, notice):
        """Process a grant Notice from the server."""
        # Processes the grant even in client mode.
        if notice.type != Notice.GRANT:
            raise TypeError("Expected a 'grant' notice")
        self._grant(notice.data.get('players'), notice.data.get('actions'))
        return self


    def _expire(self, filters=FILTER_ALL):
        if not filters:
            return
        self.notify(self.players, Notice(type=Notice.EXPIRE, data=filters))
        for filt in tupley(filters):
            # Optimization for a common case
            if isinstance(filt, ClsFilterAll):
                self.grants = dict()
                return
            elif isinstance(filt, six.text_type):
                for g in self.grants.values():
                    g.pop(filt, None)
            else:
                for p in self.grants:
                    self.grants[p] = [ a for a in self.grants[p] if not filt.accepts(a) ]

    def expire(self, filters=FILTER_ALL):
        if not self._client_mode:
            self._expire(filters)
        return self

    def server_expire_notice(self, notice):
        """Process an expire Notice from the server."""
        # Processes the grant even in client mode.
        if notice.type != Notice.EXPIRE:
            raise TypeError("Expected an 'expire' notice")
        self._expire(notice.data)
        return self


    def trigger(self, player, id, kwargs):
        a = self.find_grant(player, id)
        if not a: return False

        self.expire(a.expires)

        # Actions can default or force certain kwargs:
        if a.kwargs or a.defaults:
            kwargs = copy.copy(kwargs)
        if a.kwargs:
            kwargs.update(a.kwargs)
        if a.defaults:
            for k, v in six.iteritems(a.defaults):
                kwargs.setdefault(k, v)

        # Finally call the action
        ok = self.call(a.name, kwargs)

        if ok and not a.repeatable:
            self.expire(a.id)

    def find_grant(self, player, id):
        """
        Find a player grant by id and returns it, else returns `None`.
        """
        if player in self.grants:
            if id in self.grants[player]:
                a = self.grants[player][id]
                if isinstance(a, Action):
                    return a
        return None

    def list_grants(self, player, filt=FILTER_ALL):
        """
        Return a tuple of player grants matching the requested filter (default all grants).
        """
        if player not in self.grants:
            return ()

        if isinstance(filt, ClsFilterAll):
            return tuple(self.grants[player].values())
        else:
            return tuple(a for a in self.grants[player].values() if filt.accepts(a))

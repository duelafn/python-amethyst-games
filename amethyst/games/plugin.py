# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0

__all__ = """
EnginePlugin
action
event_listener
""".split()

import copy

import amethyst.core.obj
from amethyst.core import Object, Attr, cached_property

from amethyst.games.util import PluginCompatibilityException


class event_listener(object):
    """
    Decorator for registration with the engine event dispatcher.

    When an EnginePlugin method is decorated with thie class, the plugin
    will automatically register it with the engine so that any events of
    the requested type which are sent to the engine `.dispatch()` method
    will be sent to the decorated method.

    The notice sequence number is verified by dispatch, so plugins need not
    verify the sequence in their methods.

    Create a listener for a specific call type (recommended):

        @event_listener(NoticeType.CALL)
        def foo(self, game, seq, player, notice):
            ...

    Listen to all notices:

        @event_listener
        def foo(self, game, seq, player, notice):
            ...
    """
    def __init__(self, what):
        self.cb = self.type = None
        self.seq = 0
        if callable(what):
            self.cb = what
            self.name = self.cb.__name__
        else:
            self.type = what

    def __call__(self, *args):
        if self.cb:
            return self.cb(*args)

        self.cb = args[0]
        self.name = self.cb.__name__
        return self


class action(object):
    """
    Plugin action proerty decorator.

    class MyPlugin(EnginePlugin):
        @action
        def place_robber(self, engine, stash, **kwargs):
            ...

        @place_robber.check
        def place_robber(self, engine, stash, **kwargs):
            ...

    See `Engine.call_immediate` for more details about how these are used.
    """

    def __init__(self, *args, action=None, name=None):
        self.cb = dict()
        if args:
            if action:
                raise Exception("May not specify 'action' named parameter with an unnamed argument")
            if len(args) > 1:
                raise Exception("Exptected only a single argument")
            action = args[0]
        if action:
            self.cb['action'] = action
            self.name = action.__name__
        if name is not None:
            self.name = name

    def __call__(self, *args, **kwargs):
        if 'action' in self.cb:
            raise Exception("Plugin actions are not directly callable. Factor common code into a standard method or use Engine.call_immediate(...) instead")
        elif args:
            self.cb['action'] = args[0]
            self.name = args[0].__name__


    def __contains__(self, item):
        return item in self.cb

    def call(self, cb, *args, **kwargs):
        if cb in self.cb:
            return self.cb[cb](*args, **kwargs)
        return None

    def check(self, func):
        """
        Called when immutable. Return `False` to cancel the action.

        .. note:: Any other return value, including `None`, will allow the
        action to proceed!

        .. note:: This callback may be called more than once. It amy be
        called at the time that an action is scheduled and then again just
        before executing. If needed, set a stash value as a flag to prevent
        extra work. Just keep in mind that the game state may chnge between
        calls to check.
        """
        self.cb['check'] = func
        return self

    def init(self, func):
        """
        Called when immutable. changes to the stash will be saved in the
        journal. Generate random numbers here!
        """
        self.cb['init'] = func
        return self

    def notify(self, func):
        """
        Called after acceptance and init, but before actually performing
        the action.

        Callback is passed: engine, stash, player, p_kwargs

        p_kwargs is the proposed dictionary of information to send to the
        player. The callback should return a censored or augmented
        dictionary for the player.

        Notify callbacks are called in order and each receives the
        dictionary returned by its predecessor. The final dictionary is
        what is sent to the player.

        Return `None` to break the chain and prevent notifying the client.

        Return an empty dictionary to notify the client but to send them no
        information.
        """
        self.cb['notify'] = func
        return self

    def before(self, func):
        """
        Called just before the action.
        """
        self.cb['before'] = func
        return self

    def after(self, func):
        """
        Called just after the action.
        """
        self.cb['after'] = func
        return self

    def keep(self, func):
        """
        Called after all action callbacks and before/after callbacks
        succeed. Failure here is ignored.
        """
        self.cb['keep'] = func
        return self

    def error(self, func):
        """
        Called if any action callbacks and before/after callbacks raise an
        exception. Failure here is ignored.
        """
        self.cb['error'] = func
        return self

#     def client(self, func):
#         """
#         If defined, called in lieu of the main action function when a game
#         is running in client mode.
#         """
#         self.cb['client'] = func
#         return self


class PluginMetaclass(amethyst.core.obj.AttrsMetaclass):
    def __new__(cls, class_name, bases, attrs):
        actions = dict()
        listeners = []
        for val in attrs.values():
            if isinstance(val, action):
                actions[val.name] = val
            if isinstance(val, event_listener):
                listeners.append(val)
        new_cls = super(PluginMetaclass,cls).__new__(cls, class_name, bases, attrs)
        new_cls._actions = actions
        new_cls._listeners = listeners
        return new_cls

BasePlugin = PluginMetaclass(str('BasePlugin'), (), {})


class EnginePlugin(Object, BasePlugin):
    """
    EnginePlugin

    :cvar AMETHYST_ENGINE_DEPENDS: Iterable collection of plugin class
        names (as strings) which this plugin delends on. An exception will
        be thrown if any dependencies are not available when the plugin is
        registered.
    :type AMETHYST_ENGINE_DEPENDS: Any iterable of str

    :cvar AMETHYST_ENGINE_METHODS: Iterable collection of methods to be
        added to the engine object which will be handled by this plugin. It
        is an error for multiple plugins to define the same method, so be
        considerate and try to prefix your method names to avoid
        collisions.
    :type AMETHYST_ENGINE_METHODS: Any iterable of str

    :cvar AMETHYST_PLUGIN_COMPAT: Plugin version number as a float or int.
        Plugin version compatibility between instances is ensured via the
        integer portion of this value. (See `compat`)
    :type AMETHYST_PLUGIN_COMPAT: float or int

    :ivar compat: Version number of instance. When plugin data is
        deserialized, this value is compared against the class variable
        `AMETHYST_PLUGIN_COMPAT`. If they do not have the same integer
        value, an exception will be thrown.
    """
    AMETHYST_ENGINE_DEPENDS = ()
    AMETHYST_ENGINE_METHODS = ()
    AMETHYST_ENGINE_DEFAULT_METHOD_PREFIX = ""
    AMETHYST_ENGINE_DEFAULT_METHOD_SUFFIX = ""
    # Compatibility: class attr hard-coded, instance attr used when passing
    # constructed objects over the wire. Allows server to verify that the
    # server plugin version is compatible with the client plugin version.
    AMETHYST_PLUGIN_COMPAT  = None
    compat = Attr(float)

    def __init__(self, *args, **kwargs):
        self.amethyst_method_prefix = kwargs.pop("amethyst_method_prefix", self.AMETHYST_ENGINE_DEFAULT_METHOD_PREFIX)
        self.amethyst_method_suffix = kwargs.pop("amethyst_method_suffix", self.AMETHYST_ENGINE_DEFAULT_METHOD_SUFFIX)
        super(EnginePlugin,self).__init__(*args, **kwargs)
        if self.compat is None:
            self.compat = self.AMETHYST_PLUGIN_COMPAT
        if self.AMETHYST_PLUGIN_COMPAT is None:
            raise PluginCompatibilityException("Plugin {} does not define an api version".format(self.__class__.__name__))
        if int(self.compat) != int(self.AMETHYST_PLUGIN_COMPAT):
            raise PluginCompatibilityException("Plugin {} imported incompatible serialized data: Loaded {} data, this is version {}".format(self.__class__.__name__, self.compat, self.AMETHYST_PLUGIN_COMPAT))

    def make_mutable(self):
        self.amethyst_make_mutable()
    def make_immutable(self):
        self.amethyst_make_immutable()

    def _listener_callback(self, listener):
        def cb(*args):
            listener(self, *args)
        cb.__name__ = listener.name
        return cb
    def on_assign_to_game(self, game):
        for listener in self._listeners:
            game.register_event_listener(listener.type, self._listener_callback(listener))

    def initialize_early(self, game, attrs=None):
        pass

    def initialize(self, game, attrs=None):
        if attrs is not None:
            self.load_data(attrs, verifyclass=False)

    def initialize_late(self, game, attrs=None):
        pass

    @cached_property
    def initialization_data(self):
        return None

    def get_state(self, player):
        return copy.deepcopy(self.dict)

    def set_state(self, state):
        self.set(**state)



def event_listener1(typ):
    def decorate(meth):
        meth.event_listener = typ
        return meth
    return decorate

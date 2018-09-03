# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
from __future__ import division, absolute_import, print_function, unicode_literals

__all__ = """
EnginePlugin
event_listener
""".split()

import copy
import six

from amethyst.core import Object, Attr, cached_property

from .util import PluginCompatibilityException


class EnginePlugin(Object):
    """EnginePlugin

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

    def initialize(self, game, attrs=None):
        for name in dir(self):
            attr = getattr(self, name)
            if hasattr(attr, "event_listener"):
#                 print(attr.event_listener, "->", name)
                game.register_event_listener(attr.event_listener, attr)

        if attrs is not None:
            self.load_data(attrs, verifyclass=False)

    @cached_property
    def initialization_data(self):
        return None

    def get_state(self, player):
        return copy.deepcopy(self.dict)

    def set_state(self, state):
        self.set(**state)



def event_listener(typ):
    def decorate(meth):
        meth.event_listener = typ
        return meth
    return decorate


class event_listener2(object):
    """
    Enables automatic registration with the engine event dispatcher.

    When an EnginePlugin method is decorated with thie class, the plugin
    will automatically register it with the engine so that any events of
    the requested type which are sent to the engine `.dispatch_event()`
    method will be sent to the decorated method.

    The notice sequence number is verified by dispatch_event, so plugins
    need not verify the sequence in their methods.

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
        else:
            self.type = what

    def __call__(self, *args):
        if self.cb:
            return self.cb(*args)

        self.cb = args[0]
        return self

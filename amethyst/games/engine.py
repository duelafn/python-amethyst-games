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

__all__ = 'Engine EnginePlugin InvalidActionException'.split()

import six
from collections import defaultdict

import amethyst.games.plugin
from amethyst.core import Object, Attr

class InvalidActionException(Exception):
    pass

class EnginePlugin(Object):
    AMETHYST_PLUGIN_COMPAT  = None
    AMETHYST_ENGINE_METHODS = ()
    AMETHYST_ENGINE_DEPENDS = ()
    compat = Attr(isa=six.text_type)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.compat is None:
            self.compat = self.AMETHYST_PLUGIN_COMPAT
        if self.AMETHYST_PLUGIN_COMPAT is None:
            raise Exception("Plugin {} does not define an api version".format(self.__class__.__name__))
        if self.compat != self.AMETHYST_PLUGIN_COMPAT:
            raise Exception("Plugin {} imported incompatible serialized data: Loaded {} data, this is version {}".format(self.__class__.__name__, self.compat, self.AMETHYST_PLUGIN_COMPAT))


ENGINE_CALL_ORDER = "BEFORE ACTION AFTER".split()
ENGINE_CALL_TYPES = ENGINE_CALL_ORDER + "CHECK UNDO".split()

class Engine(Object):
    role = Attr(isa=six.text_type)
    actions = Attr(builder=lambda: defaultdict(list))
    plugins = Attr(builder=set)
    plugin_names = Attr(builder=set)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = dict()
        self.plugin_pkgs = [ amethyst.games.plugin ]
        for plugin in self.plugins:
            self.register(plugin)

    def start(self):
        for plugin in self.plugins:
            if hasattr(plugin, "start_game"):
                plugin.start_game(self)

    def call(self, name, **kwargs):
        """
        Call an action by name. Raises an exception if action does not exist.
        """
        actions = self.actions.get(name)
        if actions is None:
            raise Exception("No such action '{}'".format(name))
        for cb in actions["CHECK"]:
            try:
                cb(self, **kwargs)
            except InvalidActionException:
                return False

        for stage in ENGINE_CALL_ORDER:
            if stage in actions:
                for cb in actions[stage]:
                    cb(self, **kwargs)
        return True

    def insert_plugin_package(self, *pkgs):
        """
        Prepends one or more packages to the list searched for named plugins.
        """
        self.plugin_pkgs[:0] = pkgs

    def isa(self, cls, *args, **kwargs):
        """
        Register a plugin by name. Searches registered plugin packages and
        initializes an instance from the passed arguments.
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

        for dep in plugin.AMETHYST_ENGINE_DEPENDS:
            if dep not in self.plugins:
                raise Exception("Plugin {} requires plugin {}".format(name, dep))

        for attr in plugin.AMETHYST_ENGINE_METHODS:
            if hasattr(self, attr):
                raise Exception("Engine already has a method '{}' (attempted override by {})".format(attr, name))
            self._register_method(attr, plugin)

        for attr in dir(plugin):
            for prefix in ENGINE_CALL_TYPES:
                if attr.startswith(prefix + "_"):
                    action = attr[(1+len(prefix)):]
                    if action not in self.actions:
                        self.actions[action] = dict()
                    if prefix not in self.actions[action]:
                        self.actions[action][prefix] = list()

                    self.actions[action][prefix].append(getattr(plugin, attr))

    def _register_method(self, name, plugin):
        """Method exists just to make closure work"""
        setattr(
            self, name,
            lambda *args, **kwargs: getattr(plugin, name)(self, *args, **kwargs)
        )

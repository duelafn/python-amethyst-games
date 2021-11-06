# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
__all__ = 'Notice NoticeType'.split()

import warnings

from amethyst.core import Attr

from amethyst_games.filters import Filterable
from amethyst_games.util import AmethystGameException

class NoticeType(object):
    _tokens = dict()

    @classmethod
    def register(self, **kwargs):
        """
        Register a notice type, mapping an identifier to a type.
        Registration is optional, but recommended. Example:

            NoticeType.register(DO_SOMETHING='dosomething')

        Registration installs an attribute on `NoticeType` using the
        identifier whose value is the provided type string. The attribute
        can be used when constructing notices,

            Notice(type=NoticeType.DO_SOMETHING, ...)

        The identifier (key) must be a valid python identifier in all
        upper-case. The type (value) is a string which will be the actual
        notice type.

        Notice types declared in `amethyst_gamess` will all be prefixed by
        two colons, as in `NoticeType.register(CALL="::call")`. Other
        libraries should prefix with a single colon and their library name,
        including at least one dot:

            NoticeType.register(PING=":mylib.ping")`

        Actual games are free to use any type string they like, but are
        discouraged from using type strings that start with a colon unless
        they follow the library rules above.
        """
        for key, token in kwargs.items():
            if not key.isidentifier():
                raise AmethystGameException("Notice type must be a valid identifier, got '{}'".format(key))
            if key != key.upper():
                raise AmethystGameException("Notice type must be upper-case, got '{}'".format(key))
            if hasattr(self, key):
                if token == getattr(self, key):
                    warnings.warn("Duplicate notice type declaration of '{}'".format(key))
                    continue
                else:
                    raise AmethystGameException("Notice type '{}' already registered".format(key))
            if token in self._tokens:
                raise AmethystGameException("Notice token '{}' already used by type '{}', can not also register to '{}'".format(token, self._tokens[token], key))

            setattr(self, key, token)
            self._tokens[token] = key

    @classmethod
    def names(self):
        """
        Returns an iterable of all known types (e.g., GRANT, CALL, STORE_SET, ...).
        """
        return self._tokens.values()

    @classmethod
    def items(self):
        """Iterate known identifiers and types, like dict.items()."""
        for name in self.names():
            yield (name, getattr(self, name))


class Notice(Filterable):
    source = Attr(isa=str)
    data = Attr(isa=dict)

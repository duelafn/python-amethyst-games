# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0

__all__ = """

IFilter
   Filter
   ClsFilterAll FILTER_ALL

Filterable

""".split()

from amethyst.core import Object, Attr

from .util import nonce, tupley



class IFilter(Object):
    """
    IFilter - filter interface

    Defines required methods for filters.
    """

    def accepts(self, obj):
        return False

class ClsFilterAll(IFilter):
    def accepts(self, obj):
        return True
FILTER_ALL = ClsFilterAll()

class Filter(IFilter):
    """
    Filter
    """
    id    = Attr()
    name  = Attr()
    flag  = Attr()
    any   = Attr()
    all   = Attr()

    def __init__(self, *args, **kwargs):
        super(Filter,self).__init__(*args, **kwargs)
        self.make_immutable()
    def make_immutable(self):
        self.amethyst_make_immutable()

    def accepts(self, obj):
        rv = []
        rv.append(self.test_item(self.id, obj.id))
        if rv[-1] is False: return False

        rv.append(self.test_item(self.name, obj.name))
        if rv[-1] is False: return False

        rv.append(self.test_set(self.flag, obj.flags))
        if rv[-1] is False: return False

        if self.any:
            rv.append(any(filt.accepts(obj) for filt in self.any))
            if rv[-1] is False: return False

        if self.all:
            rv.append(all(filt.accepts(obj) for filt in self.all))
            if rv[-1] is False: return False

        # We break early if we get any failures (False), so all items in rv
        # are either True or None, thus we just have to look to see whether
        # any of the test above had anything to say about the test object.
        return True if any(rv) else None

    def test_item(self, test, val):
        if test is None: return None
        if isinstance(test, str):
            return test == val
        if isinstance(test, (list, tuple, set, frozenset)):
            return val in test
        raise TypeError("Not Implemented")

    def test_set(self, test, vals):
        if test is None: return None
        if isinstance(test, str):
            return test in vals
        if isinstance(test, (list, tuple)):
            for t in test:
                if t not in vals:
                    return False
            return True
        if isinstance(test, (set, frozenset)):
            for t in test:
                if t in vals:
                    return True
            return False
        raise TypeError("Not Implemented")

class Filterable(Object):
    id = Attr(isa=str, default=nonce)
    name = Attr(isa=str)
    flags = Attr(isa=set, default=set)

    def __init__(self, *args, **kwargs):
        super(Filterable,self).__init__(*args, **kwargs)
        self.make_immutable()
    def make_immutable(self):
        self.amethyst_make_immutable()

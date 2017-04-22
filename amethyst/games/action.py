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
from __future__ import division, absolute_import, print_function, unicode_literals

__all__ = """

IFilter
   Filter
   ClsFilterAll FILTER_ALL

Filterable
   Achievement
   Action

""".split()

import six

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
        if isinstance(test, six.string_types):
            return test == val
        if isinstance(test, (list, tuple, set, frozenset)):
            return val in test
        raise TypeError("Not Implemented")

    def test_set(self, test, vals):
        if test is None: return None
        if isinstance(test, six.string_types):
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
    _ensure_flags_ = frozenset()
    id = Attr(isa=six.text_type, default=nonce)
    name = Attr(isa=six.text_type)
    flags = Attr(isa=set, default=set)

    def __init__(self, *args, **kwargs):
        super(Filterable,self).__init__(*args, **kwargs)
        if self._ensure_flags_:
            if self.flags is None:
                self.flags = set(self._ensure_flags_)
            else:
                self.flags.update(self._ensure_flags_)
        self.make_immutable()


class Achievement(Filterable):
    _ensure_flags_ = frozenset(["Achievement"])

    @classmethod
    def from_action(cls, action):
        init = dict(id=action.id)
        if action.name: init['name'] = action.name
        if action.flags: init['flags'] = set(action.flags)
        return cls(init)

class Action(Filterable):
    _ensure_flags_ = frozenset(["Action"])

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

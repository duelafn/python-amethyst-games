# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0

__all__ = """

IFilter
   Filter
   FILTER_ALL

IFilterable
   Filterable

""".split()

from amethyst.core import Object, Attr

from amethyst.games.util import nonce



class IFilter(object):
    """
    IFilter - filter interface

    Defines required methods for filters and implements logical operators
    on Filters.
    """
    def accepts(self, obj):
        return False


    def __and__(self, other):
        if not isinstance(other, IFilter):
            raise Exception("Can only & a Filter with another Filter")
        return AndFilter(left=self, right=other)

    def __or__(self, other):
        if not isinstance(other, IFilter):
            raise Exception("Can only | a Filter with another Filter")
        return OrFilter(left=self, right=other)

    def __xor__(self, other):
        if not isinstance(other, IFilter):
            raise Exception("Can only ^ a Filter with another Filter")
        return XorFilter(left=self, right=other)

    def __invert__(self):
        return NotFilter(filter=self)


class ClsFilterAll(IFilter):
    def accepts(self, obj):
        return True


FILTER_ALL = ClsFilterAll()


class BinOpFilter(IFilter, Object):
    left = Attr()
    right = Attr()

class AndFilter(BinOpFilter):
    def accepts(self, obj):
        return bool(self.left.accepts(obj)) and bool(self.right.accepts(obj))

class OrFilter(BinOpFilter):
    def accepts(self, obj):
        return bool(self.left.accepts(obj)) or bool(self.right.accepts(obj))

class XorFilter(BinOpFilter):
    def accepts(self, obj):
        return bool(self.left.accepts(obj)) ^ bool(self.right.accepts(obj))

class NotFilter(IFilter, Object):
    filter = Attr()
    def accepts(self, obj):
        return not bool(self.filter.accepts(obj))

class Filter(IFilter, Object):
    """
    Filter

    If more than one attribute is set, then all must accept the filterable.

    :ivar id: When a string, accepts any filterable with the given id. When
    a list, tuple, set, or frozenset, accepts any filterable whose id is
    listed.

    :ivar name: When a string, accepts any filterable with the given name.
    When a list, tuple, set, or frozenset, accepts any filterable whose
    name is listed.

    :ivar flag: When a string, accepts any filterable with the given flag.
    When a list or tuple, accepts any filterable with ALL of the listed
    flags. When a set, or frozenset, accepts any filterable with ANY of the
    listed flags.

    :ivar any: An iterable of `Filter`, will accept any filterable as long
    as ANY of the listed filters accepts the filterable.

    :ivar all: An iterable of `Filter`, will accept any filterable as long
    as ALL of the listed filters accepts the filterable.
    """
    id    = Attr()
    name  = Attr()
    type  = Attr()
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

        rv.append(self.test_item(self.type, obj.type))
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
        if val is None: return False
        if isinstance(test, str):
            return test == val
        if isinstance(test, (list, tuple, set, frozenset)):
            return val in test
        raise TypeError("Not Implemented")

    def test_set(self, test, vals):
        if test is None: return None
        if vals is None: return False
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


class IFilterable(object):
    """
    Filterable interface.

    This class merely defines the interface. Most objects should subclass
    `Filterable` which is also an `amethyst.core.Object`.

    The following attributes are defined by this interface but always
    return None, thus will only be matchable if the filter does not try to
    match it.

    :ivar str id: Stable, globally unique identifier.

    :ivar str name: Object name, not assumed to be unique.

    :ivar str type: Object type, not assumed to be unique.

    :ivar set flags: Arbitrary set of string flags or tags describing the
    filterable. The core amethyst libraries accept a frozenset as well. The
    core amethyst libraries will typically also accept a list or tuple
    value, though possibly with reduced performance.
    """
    @property
    def id(self):
        None
    @property
    def name(self):
        None
    @property
    def type(self):
        None
    @property
    def flags(self):
        None


class Filterable(IFilterable, Object):
    """
    Filterable base Object.

    The object will be set immutable in the constructor (though see
    limitations in the `amethyst.core` documentation).

    If an `id` is not passed to the constructor, a random one will be
    generated.

    `name` and `type` will default to `None` and `flags weill default to an
    empty `set()`.
    """
    id = Attr(isa=str, default=nonce, OVERRIDE=True)
    name = Attr(isa=str, OVERRIDE=True)
    type = Attr(isa=str, OVERRIDE=True)
    flags = Attr(isa=set, default=set, OVERRIDE=True)

    def __init__(self, *args, **kwargs):
        super(Filterable,self).__init__(*args, **kwargs)
        self.make_immutable()
    def make_immutable(self):
        self.amethyst_make_immutable()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0

import sys
import unittest

from os.path import dirname, abspath
sys.path.insert(1, dirname(dirname(abspath(__file__))))

import amethyst.core

from amethyst.games.filters import Filter, Filterable

class TestFilters(unittest.TestCase):
    def test_filters(self):
        foo = Filterable(name="Foo", flags=set("abc"))
        bar = Filterable(name="Bar", flags=set("cde"))

        # Filterables are immutable by default:
        with self.assertRaises(amethyst.core.ImmutableObjectException):
            foo.name = "Baz"

        foo_filter = Filter(name="Foo")
        self.assertTrue(foo_filter.accepts(foo))
        self.assertFalse(foo_filter.accepts(bar))

        self.assertTrue(Filter(flag="a").accepts(foo))
        self.assertTrue(Filter(flag=["a","b"]).accepts(foo))
        self.assertFalse(Filter(flag=["a","d"]).accepts(foo))
        self.assertTrue(Filter(flag=set(["a","d"])).accepts(foo))

        self.assertTrue(Filter(id=foo.id).accepts(foo))
        self.assertFalse(Filter(id=foo.id).accepts(bar))

        f = Filter(id=foo.id) & Filter(name="Foo")
        self.assertTrue(f.accepts(foo))
        self.assertFalse(f.accepts(bar))

        f = ~f
        self.assertFalse(f.accepts(foo))
        self.assertTrue(f.accepts(bar))

        f = Filter(id=foo.id) | Filter(name="Bar")
        self.assertTrue(f.accepts(foo))
        self.assertTrue(f.accepts(bar))

        f = Filter(any=[Filter(id=foo.id), Filter(name="Bar")])
        self.assertTrue(f.accepts(foo))
        self.assertTrue(f.accepts(bar))

        f = Filter(id=foo.id) ^ Filter(flag="c")
        self.assertFalse(f.accepts(foo))
        self.assertTrue(f.accepts(bar))


if __name__ == '__main__':
    unittest.main()

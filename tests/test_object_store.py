#!/usr/bin/python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0
import unittest

import amethyst_games
from amethyst_games.filters import Filter, Filterable
from amethyst_games.plugins import ObjectStore


class Engine(amethyst_games.Engine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_plugin(ObjectStore())
        self.players.append(0)


class ObjectStoreListShared(unittest.TestCase):
    def setUp(self):
        self.game = Engine()

    def test_empty(self):
        self.assertEqual(self.game.stor_list_shared(), [])

    def test_list_all(self):
        objects = [
            Filterable(name='a'),
            Filterable(name='b'),
            Filterable(name='c'),
        ]
        for obj in objects:
            self.game.stor_set_shared(obj.id, obj)

        self.assertCountEqual(self.game.stor_list_shared(), objects)

    def test_with_filter(self):
        objects = [
            Filterable(name='a', flags=set('abd')),
            Filterable(name='b', flags=set('bcd')),
            Filterable(name='c', flags=set('abc')),
        ]
        for obj in objects:
            self.game.stor_set_shared(obj.id, obj)

        self.assertCountEqual(
            self.game.stor_list_shared(Filter(flag='a')),
            [objects[0], objects[2]]
        )


if __name__ == '__main__':
    unittest.main()

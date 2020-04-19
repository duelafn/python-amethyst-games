#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-3.0
import sys
if sys.version_info < (3,6):
    raise Exception("Python 3.6 required -- this is only " + sys.version)

import unittest

from os.path import dirname, abspath
sys.path.insert(1, dirname(dirname(abspath(__file__))))

from amethyst.games import action
from amethyst.games.plugins import GrantManager, Grant
import amethyst.games



class Engine(amethyst.games.Engine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_plugin(GrantManager())
        self.register_plugin(BaseGame())
        self.players.append(0)

    def Grant(self, *args, **kwargs):
        self.grant(0, Grant(*args, **kwargs))

class BaseGame(amethyst.games.EnginePlugin):
    AMETHYST_PLUGIN_COMPAT = 1  # Plugin API version

    @action
    def test_param(self, game, stash, test=None, param='something', msg=None):
        if test:
            test.counter += 1
            test.assertEqual(param, 'foo', msg=msg)
        else:
            game.Grant(name="test_param")

    @action
    def test_pass_none(self, game, stash, test=None, param='something', msg=None):
        if test:
            test.counter += 1
            test.assertIsNone(param, msg=msg)
        else:
            game.Grant(name="test_pass_none")

    @action
    def test_masking(self, game, stash, test=None, param='something', msg=None):
        if test:
            test.counter += 1
            test.assertIsNone(param, msg=msg)
        else:
            game.Grant(name="test_masking", kwargs=dict(param=None))


class TestCounts(object):
    def __init__(self, test, num):
        self.test = test
        self.num = num
    def __enter__(self):
        self.count = self.test.counter
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.test.game.process_queue()
            self.test.assertEqual(self.test.counter, self.count + self.num)


class MyTest(unittest.TestCase):
    def setUp(self):
        self.counter = 0

    def assertRunsTests(self, num):
        return TestCounts(self, num)

    def assertOneGrant(self):
        self.game.process_queue()
        grants = self.game.list_grants(0)
        self.assertEqual(len(grants), 1)
        return grants[0]

    def assertNoGrants(self):
        self.game.process_queue()
        grants = self.game.list_grants(0)
        self.assertEqual(len(grants), 0)


    def test_grant_parameters(self):
        self.game = game = Engine()

        game.call_immediate("test_param")
        grant = self.assertOneGrant()
        with self.assertRunsTests(1):
            game.trigger(0, grant.id, dict(test=self, param='foo'))
        self.assertNoGrants()

        game.call_immediate("test_masking")
        grant = self.assertOneGrant()
        with self.assertRunsTests(1):
            game.trigger(0, grant.id, dict(test=self, param='foo'))
        self.assertNoGrants()

        game.call_immediate("test_pass_none")
        grant = self.assertOneGrant()
        with self.assertRunsTests(1):
            game.trigger(0, grant.id, dict(test=self, param=None))
        self.assertNoGrants()


if __name__ == '__main__':
    unittest.main()

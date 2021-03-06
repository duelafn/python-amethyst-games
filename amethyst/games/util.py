# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
__all__ = '''

GAME_MASTER
NOBODY

nonce
random
tupley

AmethystGameException
  NotificationSequenceException
  PluginCompatibilityException
  UnknownActionException

'''.split()

import base64
import os
import threading
import weakref

from random import SystemRandom

from amethyst.core import cached_property

random = SystemRandom()

GAME_MASTER = object()   # sentinel value
NOBODY = None            # sentinel value

class AmethystGameException(Exception): pass
class NotificationSequenceException(AmethystGameException): pass
class PluginCompatibilityException(AmethystGameException): pass
class UnknownActionException(AmethystGameException): pass

def nonce():
    """
    Generate a random printable string identifier.
    Currently 20 characters long with 120 bits of entropy.
    """
    return base64.b64encode(os.urandom(15)).decode("UTF-8")

def tupley(thingun):
    """
    Make sure thingun is like a tuple - a list, set, tuple. If not, wraps
    thingun into a single-item or empty (when None) tuple.
    """
    if thingun is None:
        return ()
    if isinstance(thingun, (list, tuple, set, frozenset)):
        return thingun
    return (thingun,)


class AmethystWriteLockInstance(object):
    def __init__(self, obj, lock, make_mutable=True):
        self.obj = weakref.ref(obj)
        self.lock = lock
        self.make_mutable = make_mutable
        self.unlock = False
        self.make_immutable = False

    def __enter__(self):
        if self.lock.acquire():
            self.unlock = True
        else:
            raise Exception("Error")

        obj = self.obj()
        if self.make_mutable and not obj.amethyst_is_mutable():
            self.make_immutable = True
            try:
                obj.make_mutable()
            except Exception:
                self.lock.release()
                raise

        return obj

    def __exit__(self, exc_type, exc_value, traceback):
        if self.make_immutable:
            self.make_immutable = False
            try:
                self.obj().make_immutable()
            except Exception:
                pass
        if self.unlock:
            self.unlock = False
            self.lock.release()


class AmethystWriteLocker(object):
    @cached_property
    def _write_lock(self):
        return threading.RLock()

    def write_lock(self, make_mutable=True):
        return AmethystWriteLockInstance(self, self._write_lock, make_mutable=make_mutable)

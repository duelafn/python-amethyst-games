# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = '''

ADMIN
NOBODY

nonce
tupley

AmethystGameException
  NotificationSequenceException
  PluginCompatibilityException
  UnknownActionException

'''.split()

import base64
import random
import struct

LONGMOD = 1<<64-1

ADMIN = {}
NOBODY = None

class AmethystGameException(Exception): pass
class NotificationSequenceException(AmethystGameException): pass
class PluginCompatibilityException(AmethystGameException): pass
class UnknownActionException(AmethystGameException): pass

def nonce():
    """
    Generate a random printable string identifier.
    Currently 20 characters long with 120 bits of entropy.
    """
    # Yes, b64encode(os.random(15)) is easier, but this was fun (and runs in half the time)
    num = random.getrandbits(120)
    return base64.b64encode(struct.pack("ll", num % LONGMOD, num>>64)[0:15]).decode("UTF-8")

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

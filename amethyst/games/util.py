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
__all__ = '''
nonce
tupley
'''.split()

import base64
import random
import struct

LONGMOD = 1<<64-1

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

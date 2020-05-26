# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
__all__ = """
Pile
""".split()

import collections
import itertools

from amethyst.core import Attr

from amethyst.games.filters import Filterable, FILTER_ALL
from amethyst.games.util import random

def ctx_return(lst, n, as_list):
    """
    Return list or item, depending on number of items requested or whether
    the as_list override was passed.

    If list is empty and an item is requested, return None
    """
    if as_list or n is None or n > 1:
        return lst
    return lst[0] if lst else None


STACK_ALLOWED = (list, collections.deque)
class Pile(Filterable):
    """
    A pile of anything, draw pile, discard pile, player hand, stack of
    creatures, ...

    Randomness is provided by cryptographically secure sources.

    :ivar stack: The actual stack of items. Defaults to a list, but you
    may pass an initial deque if you need that sort of access.
    """
    stack = Attr(isa=STACK_ALLOWED, default=list)

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], STACK_ALLOWED):
            kwargs['stack'] = args.pop()
        super().__init__(*args, **kwargs)

    def __len__(self):
        return len(self.stack)
    def __getitem__(self, idx):
        return self.stack[idx]
    def __iter__(self):
        return self.stack.__iter__()
    def __reversed__(self):
        return self.stack.__reversed__()
    def __contains__(self, needle):
        return needle in self.stack

    def pick(self, n=1, *, as_list=None):
        """
        Randomly remove n items assuming stack is not shuffled.

        Note: This method is not particularly efficient. If possible,
        shuffle and pop() from your piles.

        Returns item if only one is requested, else returns list.
        """
        _n, rv = n, list()
        if isinstance(self.stack, collections.deque):
            # Can't .pop(i) a deque. Do some more work:
            tmp = list(self.stack)
            while _n > 0 and tmp:
                _n -= 1
                rv.append(tmp.pop( random.randint(0, len(tmp)-1) ))
            self.stack.clear()
            self.stack.extend(tmp)
        else:
            while _n > 0 and self.stack:
                _n -= 1
                rv.append(self.stack.pop( random.randint(0, len(self.stack)-1) ))
        return ctx_return(rv, n, as_list)

    def sample(self, n=1, *, as_list=None):
        """
        Randomly select n items with repetition assuming stack is not
        shuffled. Stack is left unmodified.

        Returns item if only one is requested, else returns list.
        """
        k = min(n, len(self.stack))
        rv = random.sample(self.stack, k) if k else []
        return ctx_return(rv, n, as_list)

    def choices(self, n=1, *, as_list=None):
        """
        Randomly select n items without repetition assuming stack is not
        shuffled. Stack is left unmodified.

        Returns item if only one is requested, else returns list.
        """
        k = min(n, len(self.stack))
        rv = random.choices(self.stack, k=k) if k else []
        return ctx_return(rv, n, as_list)

    def pop(self, n=1, *, as_list=None):
        """
        Take top n items off of pile, returning them.

        Returns item if only one is requested, else returns list.

        NOTE: Pile.pop(n) is different from python's list.pop(i)! If you
        want to remove an item from the middle of a pile, use Pile.remove_at(i).
        """
        _n, rv = n, list()
        while _n > 0 and self.stack:
            _n -= 1
            rv.append(self.stack.pop())
        return ctx_return(rv, n, as_list)

    def peek(self, n=1, *, as_list=None):
        """
        Look top n items of pile without removing. Items are returned in
        list order, with the top item last.

        Returns item if only one is requested, else returns list.
        """
        if self.stack:
            j = len(self.stack)
            k = min(j, n)
            # Use itertools so we work on both list() and deque()
            rv = list(itertools.islice(self.stack, j - k, j))
        else:
            rv = list()
        return ctx_return(rv, n, as_list)

    def filter(self, filt=FILTER_ALL):
        """
        Remove items matching a Filter. Return list of the removed items.
        """
        if filt is FILTER_ALL:
            rv = list(self.stack)
            self.stack.clear()
            return rv
        remove, keep = [], []
        for item in self.stack:
            if filt.accepts(item):
                remove.append(item)
            else:
                keep.append(item)
        if remove:
            self.stack.clear()
            self.stack.extend(keep)
        return remove

    def list(self, filt=FILTER_ALL):
        """
        List items matching a Filter.
        """
        return [ x for x in self.stack if filt.accepts(x) ]

    def count(self, filt=FILTER_ALL):
        """
        Count number of items matching a filter.
        """
        n = 0
        for x in self.stack:
            if filt.accepts(x):
                n += 1
        return n

    def find(self, filt=FILTER_ALL):
        """
        Return list of indices of items matching the filter.
        """
        return [ i for (i, x) in enumerate(self.stack) if filt.accepts(x) ]

    def shuffle(self):
        random.shuffle(self.stack)

    def insert(self, idx, value):
        self.stack.insert(idx, value)

    def append(self, *args):
        self.stack.extend(args)

    def extend(self, lst):
        self.stack.extend(lst)

    def remove(self, arg):
        self.stack.remove(arg)

    def remove_at(self, i):
        """
        Note: This method is very inefficient.
        """
        if isinstance(self.stack, collections.deque):
            # Can't .pop(i) a deque. Do some more work:
            tmp = list(self.stack)
            rv = tmp.pop(i)
            self.stack.clear()
            self.stack.extend(tmp)
        else:
            return self.stack.pop(i)

    def clear(self):
        self.stack.clear()

    def get(self, idx):
        return self.stack[idx]

    def set(self, idx, value):
        self.stack[idx] = value

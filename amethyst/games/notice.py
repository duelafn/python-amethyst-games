# -*- coding: utf-8 -*-
"""

"""
# SPDX-License-Identifier: LGPL-3.0
from __future__ import division, absolute_import, print_function, unicode_literals
__all__ = 'Notice NoticeType'.split()

import six

from amethyst.core import Object, Attr

from .util import AmethystGameException

class NoticeType(object):
    _tokens = dict()

    @classmethod
    def register(self, **kwargs):
#         import sys, traceback
#         traceback.print_stack()
#         sys.stderr.write("FOO " + str([ f for f in dir(self) if not f.startswith("_")]) + " " + str(kwargs) + "\n")
        for key, token in six.iteritems(kwargs):
            if hasattr(self, key):
                if token == getattr(self, key):
                    continue
                else:
                    raise AmethystGameException("Notice type '{}' already registered".format(key))
            if token in self._tokens:
                raise AmethystGameException("Notice token '{}' already used by type '{}', can not also register to '{}'".format(token, self._tokens[token], key))

            setattr(self, key, token)
            self._tokens[token] = key


class Notice(Object):
    name = Attr(isa=six.text_type)
    type = Attr(isa=six.text_type, builder=lambda: "notice")
    data = Attr(isa=dict)

    def __init__(self, *args, **kwargs):
        super(Notice,self).__init__(*args, **kwargs)
        self.make_immutable()

    def make_immutable(self):
        self.amethyst_make_immutable()

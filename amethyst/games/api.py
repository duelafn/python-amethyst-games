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

__all__ = 'Request Response'.split()

import six

from amethyst.core import Object, Attr

UNKNOWN = 800

class Request(Object):
    id  = Attr(isa=six.text_type)
    req = Attr(isa=six.text_type)
    arg = Attr()

    def build_response(self, code=UNKNOWN, msg=None, ok=None, rv=None):
        res = Response(
            res = self.req,
            code = code,
            ok = (200 <= code < 300 if ok is None else ok),
        )
        if self.id is not None:
            res.id = self.id
        if msg is not None:
            res.add_message(msg)
        if rv is not None:
            res.rv = rv
        return res


class Response(Object):
    res  = Attr(isa=six.text_type)
    ok   = Attr(bool, default=False)
    code = Attr(int, default=UNKNOWN)
    msgs = Attr()
    rv   = Attr()
    id   = Attr(isa=six.text_type)

    def accept(self, rv=None, code=None, msg=None):
        self.ok = True
        if code is not None:
            self.code = code
        if rv is not None:
            self.rv = rv
        if msg is not None:
            self.add_message(msg)

    def reject(self, code, rv=None, msg=None):
        self.ok = False
        self.code = code
        if rv is not None:
            self.rv = rv
        if msg is not None:
            self.add_message(msg)

    def add_message(self, *msgs):
        self.setdefault("msgs", [])
        for msg in msgs:
            if msg:
                if isinstance(msg, six.string_types):
                    self.msgs.append(msg)
                else:
                    self.msgs.extend(msg)

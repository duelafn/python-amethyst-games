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
__all__ = 'Notice'.split()

import six

from amethyst.core import Object, Attr

class Notice(Object):
    name = Attr(isa=six.text_type)
    type = Attr(isa=six.text_type, builder=lambda: "notice")
    data = Attr(isa=dict)

    GRANT  = ':grant'
    EXPIRE = ':expire'
    CALL   = ':call'
    MSG    = ':msg'

    def __init__(self, *args, **kwargs):
        super(Notice,self).__init__(*args, **kwargs)
        self.make_immutable()

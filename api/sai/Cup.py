# This file is part of "maker.py".
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from api.Address import Address
from api.Wad import Wad


class Cup:
    def __init__(self, lad: Address, art: Wad, ink: Wad):
        assert(isinstance(lad, Address))
        assert(isinstance(art, Wad))
        assert(isinstance(ink, Wad))
        self.lad = lad
        self.art = art
        self.ink = ink

    def __repr__(self):
        return f"Cup(lad={repr(self.lad)}, art={self.art}, ink={self.ink})"

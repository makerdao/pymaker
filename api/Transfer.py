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


class Transfer:
    """Represents an ERC20 token transfer.

    Attributes:
        token_address: Address of the token that has been transferred.
        from_address: Source address of the transfer.
        to_address: Destination address of the transfer.
        value: Value transferred.
    """
    def __init__(self, token_address: Address, from_address: Address, to_address: Address, value: Wad):
        assert(isinstance(token_address, Address))
        assert(isinstance(from_address, Address))
        assert(isinstance(to_address, Address))
        assert(isinstance(value, Wad))
        self.token_address = token_address
        self.from_address = from_address
        self.to_address = to_address
        self.value = value

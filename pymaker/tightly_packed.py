# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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

from eth_abi.encoding import encode_uint_256, BytesEncoder, AddressEncoder

from pymaker import Address


def encode_address(address: Address) -> bytes:
    return AddressEncoder().encode(address.address)[12:]


def encode_uint256(value: int) -> bytes:
    return encode_uint_256.encode(value)


def encode_bytes(value: bytes) -> bytes:
    return BytesEncoder().encode(value)

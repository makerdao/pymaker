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

from eth_abi.encoding import get_single_encoder

from pymaker import Address


def encode_address(address: Address) -> bytes:
    return get_single_encoder("address", None, None)(address.address)[12:]


def encode_uint256(value: int) -> bytes:
    return get_single_encoder("uint", 256, None)(value)


def encode_bytes(value: bytes) -> bytes:
    return get_single_encoder("bytes", len(value), None)(value)

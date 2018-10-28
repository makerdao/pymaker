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

from typing import Tuple

from eth_account.messages import defunct_hash_message
from eth_utils import encode_hex
from web3 import Web3

from pymaker import Address
from pymaker.keys import _registered_accounts
from pymaker.util import bytes_to_hexstring


def eth_sign(message: bytes, web3: Web3):
    assert(isinstance(message, bytes))
    assert(isinstance(web3, Web3))

    local_account = _registered_accounts.get((web3, Address(web3.eth.defaultAccount)))

    if local_account:
        message_hash = defunct_hash_message(primitive=message)
        signature = web3.eth.account.signHash(message_hash, private_key=local_account.privateKey).signature.hex()

        return signature

    else:
        signature = bytes_to_hexstring(web3.manager.request_blocking(
            "eth_sign", [web3.eth.defaultAccount, encode_hex(message)],
        ))

        # for `EthereumJS TestRPC/v2.2.1/ethereum-js`
        if signature.endswith("00"):
            signature = signature[:-2] + "1b"

        if signature.endswith("01"):
            signature = signature[:-2] + "1c"

        return signature


def to_vrs(signature: str) -> Tuple[int, bytes, bytes]:
    assert(isinstance(signature, str))
    assert(signature.startswith("0x"))

    signature_hex = signature[2:]
    r = bytes.fromhex(signature_hex[0:64])
    s = bytes.fromhex(signature_hex[64:128])
    v = ord(bytes.fromhex(signature_hex[128:130]))

    return v, r, s

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

import eth_keyfile
from eth_utils import coerce_return_to_text, encode_hex
from ethereum import utils
from ethereum.tester import k0
from ethereum.utils import int_to_bytes
from secp256k1 import PrivateKey
from web3 import Web3
from web3.eth import Eth

from pymaker.util import hexstring_to_bytes


def eth_sign(message: bytes, web3: Web3):
    assert(isinstance(message, bytes))
    assert(isinstance(web3, Web3))

    signature = web3.manager.request_blocking(
        "eth_sign", [web3.eth.defaultAccount, encode_hex(message)],
    )

    # for `EthereumJS TestRPC/v2.2.1/ethereum-js`
    if signature.endswith("00"):
        signature = signature[:-2] + "1b"

    if signature.endswith("01"):
        signature = signature[:-2] + "1c"

    return signature


@coerce_return_to_text
def eth_sign_with_keyfile(message: bytes, raw: bool, keyfile: str, password: str):
    assert(isinstance(message, bytes))
    assert(isinstance(raw, bool))
    assert(isinstance(keyfile, str))
    assert(isinstance(password, str))

    if not raw:
        message = hexstring_to_bytes(Eth._recoveryMessageHash(data=message))

    key = eth_keyfile.decode_keyfile_json(eth_keyfile.load_keyfile(keyfile), bytes(password, 'utf-8'))
    pk = PrivateKey(key, raw=True)
    signature = pk.ecdsa_recoverable_serialize(
        pk.ecdsa_sign_recoverable(message, raw=True)
    )

    signature = signature[0] + utils.bytearray_to_bytestr([signature[1]])
    signature_hex = signature.hex()[0:128] + int_to_bytes(ord(bytes.fromhex(signature.hex()[128:130]))+27).hex()

    return '0x' + signature_hex


def to_vrs(signature: str) -> Tuple[int, bytes, bytes]:
    assert(isinstance(signature, str))
    assert(signature.startswith("0x"))

    signature_hex = signature[2:]
    r = bytes.fromhex(signature_hex[0:64])
    s = bytes.fromhex(signature_hex[64:128])
    v = ord(bytes.fromhex(signature_hex[128:130]))

    return v, r, s

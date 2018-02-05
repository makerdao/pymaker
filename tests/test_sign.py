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

import py
from pytest import fixture
from web3 import Web3, EthereumTesterProvider

from pymaker.sign import eth_sign, eth_sign_with_keyfile


@fixture
def datadir(request):
    return py.path.local(request.module.__file__).join("..").join("data")


def test_signing(datadir):
    try:
        from sha3 import keccak_256
    except ImportError:
        from sha3 import sha3_256 as keccak_256

    # given
    web3 = Web3(EthereumTesterProvider())
    web3.eth.defaultAccount = web3.eth.accounts[0]

    # and
    text = "abc"
    msg = bytes(text, 'utf-8')
    msg_raw = keccak_256(b'\x19Ethereum Signed Message:\n' + str(len(text)).encode('utf-8') + text.encode("utf-8")).digest()

    # and
    keyfile = str(datadir.join("test_key.json"))
    password = "123456"

    # and
    expected_signature = "0x1ca03a12406951a3545b3154e3a544c9b9af677351395facd56a42c3f0b0aae1056b9a2f52ffe81ccd2829fac6446e2c73ca9fe7102fd6341a6408208520ad121b"

    # expect
    assert eth_sign(msg, web3) == expected_signature
    assert eth_sign_with_keyfile(msg, False, keyfile, password) == expected_signature
    assert eth_sign_with_keyfile(msg_raw, True, keyfile, password) == expected_signature

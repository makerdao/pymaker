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

import pkg_resources
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.keys import register_key_file
from pymaker.sign import eth_sign


def test_signing():
    # given
    web3 = Web3(HTTPProvider("http://localhost:8555"))
    web3.eth.defaultAccount = web3.eth.accounts[0]

    # and
    text = "abc"
    msg = bytes(text, 'utf-8')

    # expect
    assert eth_sign(msg, web3).startswith("0x")


def test_signing_with_key_and_rpc_should_return_same_result():
    # given
    web3 = Web3(HTTPProvider("http://localhost:8555"))
    web3.eth.defaultAccount = web3.eth.accounts[0]

    assert Address(web3.eth.defaultAccount) == Address('0x9596c16d7bf9323265c2f2e22f43e6c80eb3d943')

    # and
    text = "abc"
    msg = bytes(text, 'utf-8')

    rpc_signature = eth_sign(msg, web3)

    # when
    keyfile_path = pkg_resources.resource_filename(__name__, "accounts/0_0x9596c16d7bf9323265c2f2e22f43e6c80eb3d943.json")
    passfile_path = pkg_resources.resource_filename(__name__, "accounts/pass")

    register_key_file(web3, keyfile_path, passfile_path)

    # and
    # [we do this in order to make sure that the message was signed using the local key]
    # [with `request_blocking` set to `None` any http requests will basically fail]
    web3.manager.request_blocking = None

    # and
    local_signature = eth_sign(msg, web3)

    # then
    assert rpc_signature == local_signature

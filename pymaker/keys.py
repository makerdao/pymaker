# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018 reverendus
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

import getpass
from typing import Optional

from eth_account import Account
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from pymaker import Address

_registered_accounts = {}


def register_keys(web3: Web3, keys: Optional[list]):
    for key in keys or []:
        register_key(web3, key)


def register_key(web3: Web3, key: str):
    assert(isinstance(web3, Web3))

    parsed = {}
    for p in key.split(","):
        var, val = p.split("=")
        parsed[var] = val

    register_key_file(web3, parsed.get('key_file'), parsed.get('pass_file', None))


def register_key_file(web3: Web3, key_file: str, pass_file: Optional[str] = None):
    assert(isinstance(web3, Web3))
    assert(isinstance(key_file, str))
    assert(isinstance(pass_file, str) or (pass_file is None))

    with open(key_file) as key_file_open:
        read_key = key_file_open.read()
        if pass_file:
            with open(pass_file) as pass_file_open:
                read_pass = pass_file_open.read().replace("\n", "")
        else:
            read_pass = getpass.getpass(prompt=f"Password for {key_file}: ")

        private_key = Account.decrypt(read_key, read_pass)
        register_private_key(web3, private_key)


def register_private_key(web3: Web3, private_key):
    assert(isinstance(web3, Web3))

    account = Account.privateKeyToAccount(private_key)

    _registered_accounts[(web3, Address(account.address))] = account
    web3.middleware_stack.add(construct_sign_and_send_raw_middleware(account))

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

from eth_account import Account
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from pymaker import Address

_registered_accounts = {}


def register_key(web3: Web3, keyfile_path: str, passfile_path: str):
    assert(isinstance(web3, Web3))
    assert(isinstance(keyfile_path, str))
    assert(isinstance(passfile_path, str))

    with open(keyfile_path) as keyfile:
        with open(passfile_path) as passfile:
            read_key = keyfile.read()
            read_pass = passfile.read()

            private_key = Account.decrypt(read_key, read_pass)
            account = Account.privateKeyToAccount(private_key)

            web3.middleware_stack.add(construct_sign_and_send_raw_middleware(account))
            _registered_accounts[(web3, Address(account.address))] = account

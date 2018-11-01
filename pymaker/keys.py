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
from web3.utils.toolz import assoc, compose, curry
from web3.utils.transactions import fill_transaction_defaults

from pymaker import Address

_registered_accounts = {}


@curry
def _parity_aware_fill_nonce(is_parity, web3, transaction):
    if 'from' in transaction and 'nonce' not in transaction:
        if is_parity:
            next_nonce = web3.manager.request_blocking("parity_nextNonce", [transaction['from']])

        else:
            next_nonce = web3.eth.getTransactionCount(transaction['from'], block_identifier='pending')

        return assoc(transaction, 'nonce', next_nonce)

    else:
        return transaction


def _construct_local_sign_middleware(is_parity):

    def local_sign_middleware(make_request, w3):

        fill_tx = compose(
            fill_transaction_defaults(w3),
            _parity_aware_fill_nonce(is_parity)(w3))

        def middleware(method, params):
            if method == "eth_sendTransaction":
                transaction = fill_tx(params[0])

                if 'from' not in transaction:
                    return make_request(method, params)

                elif (w3, Address(transaction.get('from'))) not in _registered_accounts:
                    return make_request(method, params)

                account = _registered_accounts[(w3, Address(transaction.get('from')))]
                raw_tx = account.signTransaction(transaction).rawTransaction

                return make_request("eth_sendRawTransaction", [raw_tx])

            else:
                return make_request(method, params)

        return middleware

    return local_sign_middleware


def register_keys(web3: Web3, keys: Optional[list]):
    def not_none(x):
        return x if x is not None else []

    for key in not_none(keys):
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

    if "sign_and_send" not in web3.middleware_stack._queue:
        is_parity = "parity" in web3.version.node.lower()
        web3.middleware_stack.add(_construct_local_sign_middleware(is_parity), name="sign_and_send")

    with open(key_file) as key_file_open:
        read_key = key_file_open.read()
        if pass_file:
            with open(pass_file) as pass_file_open:
                read_pass = pass_file_open.read()
        else:
            read_pass = getpass.getpass()

        private_key = Account.decrypt(read_key, read_pass)
        account = Account.privateKeyToAccount(private_key)

        _registered_accounts[(web3, Address(account.address))] = account

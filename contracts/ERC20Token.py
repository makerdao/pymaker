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

from contracts.Contract import Contract
from contracts.Wad import Wad


class ERC20Token(Contract):
    abi = Contract._load_abi(__name__, 'ERC20Token.abi')
    registry = {}

    def __init__(self, web3, address):
        self.address = address
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)
        self._web3 = web3

    def name(self):
        return ERC20Token.registry.get(self.address, '???')

    def total_supply(self):
        return Wad(self._contract.call().totalSupply())

    def balance_of(self, address):
        return Wad(self._contract.call().balanceOf(address.address))

    def allowance_of(self, address, payee):
        return Wad(self._contract.call().allowance(address.address, payee.address))

    def transfer(self, address, amount):
        tx_hash = self._contract.transact().transfer(address.address, amount.value)
        return self._prepare_receipt(self._wait_for_receipt(tx_hash))

    def approve(self, address, limit):
        tx_hash = self._contract.transact().approve(address.address, limit.value)
        return self._prepare_receipt(self._wait_for_receipt(tx_hash))

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"ERC20Token(address='{self.address}')"

    @staticmethod
    def register_token(address, name):
        ERC20Token.registry[address] = name

    @staticmethod
    def token_address_by_name(token_name):
        for address, name in ERC20Token.registry.items():
            if name == token_name:
                return address
        raise Exception(f"Token {token_name} not found")

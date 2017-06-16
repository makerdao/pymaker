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

from web3 import Web3

from api.Address import Address
from api.Contract import Contract


class DSValue(Contract):
    abi = Contract._load_abi(__name__, 'DSValue.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def has_value(self) -> bool:
        return self._contract.call().peek()[1]

    def read(self):
        return self._contract.call().read()

    def read_as_hex(self) -> str:
        return ''.join(hex(ord(x))[2:].zfill(2) for x in self.read())

    def read_as_int(self) -> int:
        return int(self.read_as_hex(), 16)

    #TODO as web3.py doesn't seem to support anonymous events, monitoring for LogNote events does not work
    # def watch(self):
    #     self._contract.on("LogNote", {'filter': {'sig': bytearray.fromhex('1504460f')}}, self.__note)
    #     self._contract.pastEvents("LogNote", {'fromBlock': 0, 'filter': {'sig': bytearray.fromhex('1504460f')}}, self.__note)
    #
    #     # 'topics': ['0x1504460f00000000000000000000000000000000000000000000000000000000']
    #     # 'topics': ['0x1504460f00000000000000000000000000000000000000000000000000000000']
    #
    # def __note(self, log):
    #     args = log['args']
    #     print(args)




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


class DSValue(Contract):
    abi = Contract._load_abi(__name__, 'DSValue.abi')

    def __init__(self, web3, address):
        self.web3 = web3
        self.address = address
        self.contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def has_value(self):
        return self.contract.call().peek()[1]

    def read(self):
        return self.contract.call().read()

    def read_as_hex(self):
        return ''.join(hex(ord(x))[2:].zfill(2) for x in self.read())

    def read_as_int(self):
        return int(self.read_as_hex(), 16)

    def watch(self):
        self.contract.on("LogNote", {'filter': {'sig': bytearray.fromhex('1504460f')}}, self.__note)
        self.contract.pastEvents("LogNote", {'fromBlock': 0, 'filter': {'sig': bytearray.fromhex('1504460f')}}, self.__note)

        # 'topics': ['0x1504460f00000000000000000000000000000000000000000000000000000000']
        # 'topics': ['0x1504460f00000000000000000000000000000000000000000000000000000000']

    def __note(self, log):
        print("AAA")
        args = log['args']
        print(args)




# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 EdNoepel
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

from pymaker import Contract, Address


# TODO: Remove; this is just a mixin
class DSNote(Contract):
    """A client for the `DSNote` contract, which logs function calls as events.

    You can find the source code of the `DSNote` contract here:
    <https://github.com/dapphub/ds-note>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSNote` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSNote.abi')
    bin = Contract._load_bin(__name__, 'abi/DSNote.bin')

    @staticmethod
    def get_contract(web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))
        return Contract._get_contract(web3, DSNote.abi, address)


# This may be useful with and without DSNote
class LogNote:
    def __init__(self, log):
        self.user = Address(log['args']['user'])
        self.arg1 = log['args']['arg1']
        self.arg2 = log['args']['arg2']
        self.data = log['args']['data']
        self.raw = log

    @classmethod
    def from_event(cls, event: dict):
        assert isinstance(event, dict)

        topics = event.get('topics')

    # TODO
    # handle Note event, return LogNote object

    def __eq__(self, other):
        assert isinstance(other, LogNote)
        return self.__dict__ == other.__dict__

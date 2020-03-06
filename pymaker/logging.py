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

import logging
from pprint import pformat
from web3 import Web3
from web3._utils.events import get_event_data

from eth_abi.codec import ABICodec
from eth_abi.registry import registry as default_registry

# Shared between DSNote and many MCD contracts
class LogNote:
    def __init__(self, log):
        args = log['args']
        self.sig = Web3.toHex(args['sig'])
        self.usr = args['usr'] if 'usr' in args else None     # vat.frob doesn't offer `usr`
        self.arg1 = args['arg1'] if 'arg1' in args else None
        self.arg2 = args['arg2'] if 'arg2' in args else None
        self.arg3 = args['arg3'] if 'arg3' in args else None  # Special variant used for vat.frob
        self.block = log['blockNumber']
        self.tx_hash = log['transactionHash'].hex()
        self._data = args['data']

    @classmethod
    def from_event(cls, event: dict, contract_abi: list):
        assert isinstance(event, dict)
        assert isinstance(contract_abi, list)

        log_note_abi = [abi for abi in contract_abi if abi.get('name') == 'LogNote'][0]
        try:
            codec = ABICodec(default_registry)
            event_data = get_event_data(codec, log_note_abi, event)
            return LogNote(event_data)
        except ValueError:
            # event is not a LogNote
            return None

    def get_bytes_at_index(self, index: int) -> bytes:
        assert isinstance(index, int)
        if index > 5:
            raise ValueError("Only six words of calldata are provided")

        start_index = len(self._data) - ((6-index) * 32) - 28
        return self._data[start_index:start_index+32]

    def __eq__(self, other):
        assert isinstance(other, LogNote)
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return f"LogNote({pformat(vars(self))})"

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
from web3.utils.events import get_event_data


# Shared between DSNote and many MCD contracts
class LogNote:
    def __init__(self, log):
        self.sig = Web3.toHex(log['args']['sig'])
        self.arg1 = log['args']['arg1']
        self.arg2 = log['args']['arg2']
        self.arg3 = log['args']['arg3']
        self._data = log['args']['data']
        self._raw = log

    @classmethod
    def from_event(cls, event: dict, contract_abi: list):
        assert isinstance(event, dict)
        assert isinstance(contract_abi, list)

        topics = event.get('topics')
        if topics:
            log_note_abi = [abi for abi in contract_abi if abi.get('name') == 'LogNote'][0]
            event_data = get_event_data(log_note_abi, event)

            return LogNote(event_data)
        else:
            logging.warning(f'[from_event] Invalid topic in {event}')

    def __eq__(self, other):
        assert isinstance(other, LogNote)
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return f"LogNote({pformat(vars(self))})"

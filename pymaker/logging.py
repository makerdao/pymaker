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

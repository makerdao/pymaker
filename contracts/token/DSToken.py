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
from contracts.token.ERC20Token import ERC20Token


class DSToken(ERC20Token):
    abi = Contract._load_abi(__name__, 'DSValue.abi')

    def is_stopped(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def push(self, address, amount):
        raise NotImplementedError

    def pull(self, address, amount):
        raise NotImplementedError

    def mint(self, amount):
        raise NotImplementedError

    def burn(self, amount):
        raise NotImplementedError


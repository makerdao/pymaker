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

from typing import Optional

import array
from web3 import Web3

from api.Address import Address
from api.Contract import Contract
from api.Receipt import Receipt
from api.feed.DSValue import DSValue


class DSCache(DSValue):
    """A client for the `DSCache` contract, an expiring single-value data feed.

    As `DSCache` inherits from `DSValue`, it replicates most of its features and methods.

    You can find the source code of the `DSCache` contract here:
    <https://github.com/dapphub/ds-cache>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSCache` contract.
    """

    abi = Contract._load_abi(__name__, 'DSCache.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    #TODO implement prod() method

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


class Receipt:
    """Represents a confirmation of a successful Ethereum transaction.

    Attributes:
        transaction_hash: Hash of the Ethereum transaction.
        transfers: A list of ERC20 token transfers resulting from the execution
            of this Ethereum transaction. Each transfer is an instance of the
            `Transfer` class.
    """
    def __init__(self, transaction_hash: str, transfers: list):
        assert(isinstance(transaction_hash, str))
        assert(isinstance(transfers, list))
        self.transaction_hash = transaction_hash
        self.transfers = transfers

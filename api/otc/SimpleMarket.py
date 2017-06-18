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

import datetime
from typing import Optional

from web3 import Web3

from api.Address import Address
from api.Contract import Contract
from api.Receipt import Receipt
from api.Wad import Wad
from api.otc.OfferInfo import OfferInfo
from api.token.ERC20Token import ERC20Token


class SimpleMarket(Contract):
    """A client for a `SimpleMarket` contract.

    `SimpleMarket` is a simple on-chain OTC market for ERC20-compatible tokens.
    It powers the `OasisDEX` decentralized exchange.

    You can find the source code of the `SimpleMarket` contract here:
    <https://github.com/makerdao/maker-otc>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `SimpleMarket` contract.
    """

    abi = Contract._load_abi(__name__, 'SimpleMarket.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def get_last_offer_id(self) -> int:
        """Get the id of the last offer created on the market.

        Returns:
            The id of the last offer. Returns `0` if no offers have been created at all.
        """
        return self._contract.call().last_offer_id()

    # TODO introduce empty offer caching, as if an offer is None
    # it won't ever become not-None again
    def get_offer(self, offer_id: int) -> Optional[OfferInfo]:
        """Get the offer details.

        Args:
            offer_id: The id of the offer to get the details of.

        Returns:
            An instance of `OfferInfo` if the offer is still active, or `None` if the offer has been
            already completely taken.
        """
        array = self._contract.call().offers(offer_id)
        if array[5] is not True:
            return None
        else:
            return OfferInfo(offer_id=offer_id,
                             sell_how_much=Wad(array[0]),
                             sell_which_token=ERC20Token(web3=self.web3, address=Address(array[1])),
                             buy_how_much=Wad(array[2]),
                             buy_which_token=ERC20Token(web3=self.web3, address=Address(array[3])),
                             owner=Address(array[4]),
                             active=array[5],
                             timestamp=array[6])

    #TODO make it return the id of the newly created offer
    def make(self, have_token: Address, have_amount: Wad, want_token: Address, want_amount: Wad) -> Optional[Receipt]:
        """Create a new offer.

        The `have_amount` of `have_token` token will be taken from you on offer creation and deposited
        in the market contract. Allowance needs to be set first. Refer to the `approve()` method
        in the `ERC20Token` class.

        Args:
            have_token: Address of the ERC20 token you want to put on sale.
            have_amount: Amount of the `have_token` token you want to put on sale.
            want_token: Address of the ERC20 token you want to be paid with.
            want_amount: Amount of the `want_token` you want to receive.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the offer has been created.
            `None` if the Ethereum transaction failed.
        """
        try:
            tx_hash = self._contract.transact().make(have_token.address, want_token.address,
                                                     have_amount.value, want_amount.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def take(self, offer_id: int, quantity: Wad) -> Optional[Receipt]:
        """Takes (buys) an offer.

        If `quantity` is equal to `sell_how_much`, the whole offer will be taken (bought) which will make it
        disappear from the order book. If you want to buy a fraction of the offer, set `quantity` to a number
        lower than `sell_how_much`.

        Args:
            offer_id: Id of the offer you want to take (buy).
            quantity: Quantity of `sell_which_token` that you want to buy.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the offer has been taken (bought).
            `None` if the Ethereum transaction failed.
        """
        try:
            tx_hash = self._contract.transact().take(self._to_bytes32(offer_id), quantity.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def kill(self, offer_id: int) -> Optional[Receipt]:
        """Cancels an existing offer.

        Offers can be cancelled only by their owners. In addition to that, in case of expiring markets,
        after the market has expired all orders can be cancelled by anyone.

        Args:
            offer_id: Id of the offer you want to cancel.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the offer has been cancelled.
            `None` if the Ethereum transaction failed.
        """
        try:
            tx_hash = self._contract.transact().kill(self._to_bytes32(offer_id))
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

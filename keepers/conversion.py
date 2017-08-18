# This file is part of Maker Keeper Framework.
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

from api import Address
from api.oasis import SimpleMarket
from api.numeric import Ray
from api.numeric import Wad
from api.oasis import OfferInfo
from api.sai import Tub, Lpc, Tap
from api.token import ERC20Token


class Conversion:
    def __init__(self, source_token: Address, target_token: Address, rate: Ray, max_source_amount: Wad, method: str):
        self.source_amount = None
        self.source_token = source_token
        self.target_amount = None
        self.target_token = target_token
        self.rate = rate
        self.max_source_amount = max_source_amount
        self.method = method

    def name(self):
        raise NotImplementedError("name() not implemented")

    def execute(self):
        raise NotImplementedError("execute() not implemented")

    def address(self) -> Address:
        raise NotImplementedError("address() not implemented")

    def calldata(self) -> str:
        raise NotImplementedError("calldata() not implemented")

    def __str__(self):
        def amt(amount: Wad) -> str:
            return f"{amount} " if amount is not None else ""

        source_token_name = ERC20Token.token_name_by_address(self.source_token)
        target_token_name = ERC20Token.token_name_by_address(self.target_token)

        return f"[{amt(self.source_amount)}{source_token_name} -> {amt(self.target_amount)}{target_token_name} " \
               f"@{self.rate} by {self.method} (max={self.max_source_amount} {source_token_name})]"


class TubJoinConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(source_token=self.tub.gem(),
                         target_token=self.tub.skr(),
                         rate=(Ray.from_number(1) / tub.jar_ask()),
                         max_source_amount=Wad.from_number(1000000),  #1 mio ETH = infinity ;)
                         method="tub.join()")

    def name(self):
        return f"tub.join('{self.source_amount}')"

    def execute(self):
        return self.tub.join(self.source_amount).transact()

    def address(self) -> Address:
        return self.tub.address

    def calldata(self):
        return self.tub.join_calldata(self.source_amount)


class TubExitConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(source_token=self.tub.skr(),
                         target_token=self.tub.gem(),
                         rate=tub.jar_bid(),
                         max_source_amount=Wad.from_number(1000000),  #1 mio SKR = infinity ;)
                         method="tub.exit()")

    def name(self):
        return f"tub.exit('{self.source_amount}')"

    def execute(self):
        return self.tub.exit(self.source_amount).transact()

    def address(self) -> Address:
        return self.tub.address

    def calldata(self):
        return self.tub.exit_calldata(self.source_amount)


class TubBoomConversion(Conversion):
    def __init__(self, tub: Tub, tap: Tap):
        self.tub = tub
        self.tap = tap
        super().__init__(source_token=self.tub.skr(),
                         target_token=self.tub.sai(),
                         rate=Ray(tap.bid()),
                         max_source_amount=self.boomable_amount_in_skr(tap),
                         method="tub.boom()")

    #TODO currently the keeper doesn't see `joy` changing unless `drip` gets called
    #this is the thing `sai-explorer` is trying to calculate on his own
    def boomable_amount_in_sai(self, tap: Tap):
        return Wad.max(tap.joy() - tap.woe(), Wad.from_number(0))

    def boomable_amount_in_skr(self, tap: Tap):
        # we deduct 0.000001 in order to avoid rounding errors
        return Wad.max(Wad(self.boomable_amount_in_sai(tap) / (tap.bid())) - Wad.from_number(0.000001), Wad.from_number(0))

    def name(self):
        return f"tub.boom('{self.source_amount}')"

    def execute(self):
        return self.tap.boom(self.source_amount)

    def address(self) -> Address:
        return self.tap.address

    def calldata(self):
        return self.tap.boom_calldata(self.source_amount)


class TubBustConversion(Conversion):
    def __init__(self, tub: Tub, tap: Tap):
        self.tub = tub
        self.tap = tap
        super().__init__(source_token=self.tub.sai(),
                         target_token=self.tub.skr(),
                         rate=(Ray.from_number(1) / Ray(tap.ask())),
                         max_source_amount=self.bustable_amount_in_sai(tap),
                         method="tub.bust()")

    def bustable_amount_in_sai(self, tap: Tap):
        #TODO we always try to bust 10 SAI less than what the Tub reports
        #in order to discount the growth of `joy()` that might've have happened since the last drip
        #of course this is not the right solution and it won't even work properly if the last
        #drip happened enough time ago
        bustable_woe = tap.woe() - tap.joy() - Wad.from_number(10)

        # we deduct 0.000001 in order to avoid rounding errors
        bustable_fog = tap.fog() * tap.ask() - Wad.from_number(0.000001)

        return Wad.max(bustable_woe, bustable_fog, Wad.from_number(0))

    def name(self):
        return f"tub.bust('{self.target_amount}')"

    def execute(self):
        return self.tap.bust(self.target_amount)

    def address(self) -> Address:
        return self.tap.address

    def calldata(self):
        return self.tap.bust_calldata(self.target_amount)


class LpcTakeRefConversion(Conversion):
    def __init__(self, lpc: Lpc):
        self.lpc = lpc
        rate = Ray(self.lpc.tag() / (self.lpc.par() * self.lpc.gap()))
        #TODO we always leave 0.000001 in the liquidity pool, in case of some rounding errors
        max_entry_alt = Wad.max((ERC20Token(web3=lpc.web3, address=lpc.ref()).balance_of(lpc.address) / Wad(rate)) - Wad.from_number(0.000001), Wad.from_number(0))
        super().__init__(source_token=self.lpc.alt(),
                         target_token=self.lpc.ref(),
                         rate=rate,
                         max_source_amount=max_entry_alt,
                         method="lpc.take(ref)")

    def name(self):
        return f"lpc.take(ref, '{self.target_amount}')"

    def execute(self):
        return self.lpc.take(self.lpc.ref(), self.target_amount)

    def address(self) -> Address:
        return self.lpc.address

    def calldata(self):
        return self.lpc.take_calldata(self.lpc.ref(), self.target_amount)


class LpcTakeAltConversion(Conversion):
    def __init__(self, lpc: Lpc):
        self.lpc = lpc
        rate = Ray(self.lpc.par() / (self.lpc.tag() * self.lpc.gap()))
        #TODO we always leave 0.000001 in the liquidity pool, in case of some rounding errors
        max_entry_ref = Wad.max((ERC20Token(web3=lpc.web3, address=lpc.alt()).balance_of(lpc.address) / Wad(rate)) - Wad.from_number(0.000001), Wad.from_number(0))
        super().__init__(source_token=self.lpc.ref(),
                         target_token=self.lpc.alt(),
                         rate=rate,
                         max_source_amount=max_entry_ref,
                         method="lpc.take(alt)")

    def name(self):
        return f"lpc.take(alt, '{self.target_amount}')"

    def execute(self):
        return self.lpc.take(self.lpc.alt(), self.target_amount)

    def address(self) -> Address:
        return self.lpc.address

    def calldata(self):
        return self.lpc.take_calldata(self.lpc.alt(), self.target_amount)


class OasisTakeConversion(Conversion):
    def __init__(self, otc: SimpleMarket, offer: OfferInfo):
        self.otc = otc
        self.offer = offer
        super().__init__(source_token=offer.buy_which_token,
                         target_token=offer.sell_which_token,
                         rate=Ray(offer.sell_how_much)/Ray(offer.buy_how_much),
                         max_source_amount=offer.buy_how_much,
                         method=f"opc.take({self.offer.offer_id})")

    def name(self):
        return f"otc.take({self.offer.offer_id}, '{self.quantity()}')"

    def execute(self):
        return self.otc.take(self.offer.offer_id, self.quantity()).transact()

    def address(self) -> Address:
        return self.otc.address

    def calldata(self):
        return self.otc.take(self.offer.offer_id, self.quantity()).invocation().calldata

    def quantity(self):
        quantity = self.target_amount

        #TODO probably at some point dust order limitation will get introuced at the contract level
        #if that happens, a concept of `min_source_amount` will be needed

        # if by any chance rounding makes us want to buy more quantity than is available,
        # we just buy the whole lot
        if quantity > self.offer.sell_how_much:
            quantity = self.offer.sell_how_much

        # if by any chance rounding makes us want to buy only slightly less than the available lot,
        # we buy everything as this is probably what we wanted in the first place
        if self.offer.sell_how_much - quantity < Wad.from_number(0.0000000001):
            quantity = self.offer.sell_how_much

        return quantity

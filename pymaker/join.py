# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019-2021 EdNoepel
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

from web3 import Web3

from pymaker import Address, Contract, Transact
from pymaker.ilk import Ilk
from pymaker.token import DSToken, ERC20Token
from pymaker.numeric import Wad, Ray, Rad


logger = logging.getLogger()


class Join(Contract):
    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)
        self._token: DSToken = None

    def approve(self, approval_function, source: Address):
        assert(callable(approval_function))
        assert isinstance(source, Address)

        approval_function(ERC20Token(web3=self.web3, address=source), self.address, self.__class__.__name__)

    def approve_token(self, approval_function, **kwargs):
        return self.approve(approval_function, self._token.address, **kwargs)

    def join(self, usr: Address, value: Wad) -> Transact:
        assert isinstance(usr, Address)
        assert isinstance(value, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'join', [usr.address, value.value])

    def exit(self, usr: Address, value: Wad) -> Transact:
        assert isinstance(usr, Address)
        assert isinstance(value, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'exit', [usr.address, value.value])


class DaiJoin(Join):
    """A client for the `DaiJoin` contract, which allows the CDP holder to draw Dai from their Urn and repay it.

    Ref. <https://github.com/makerdao/dss/blob/master/src/join.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/DaiJoin.abi')
    bin = Contract._load_bin(__name__, 'abi/DaiJoin.bin')

    def __init__(self, web3: Web3, address: Address):
        super(DaiJoin, self).__init__(web3, address)
        self._token = self.dai()

    def dai(self) -> DSToken:
        address = Address(self._contract.functions.dai().call())
        return DSToken(self.web3, address)


class GemJoin(Join):
    """A client for the `GemJoin` contract, which allows the user to deposit collateral into a new or existing vault.

    Ref. <https://github.com/makerdao/dss/blob/master/src/join.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/GemJoin.abi')
    bin = Contract._load_bin(__name__, 'abi/GemJoin.bin')

    def __init__(self, web3: Web3, address: Address):
        super(GemJoin, self).__init__(web3, address)
        self._token = self.gem()

    def ilk(self):
        return Ilk.fromBytes(self._contract.functions.ilk().call())

    def gem(self) -> DSToken:
        address = Address(self._contract.functions.gem().call())
        return DSToken(self.web3, address)

    def dec(self) -> int:
        return 18


class GemJoin5(GemJoin):
    """A client for the `GemJoin5` contract, which allows the user to deposit collateral into a new or existing vault.

    Ref. <https://github.com/makerdao/dss-deploy/blob/master/src/join.sol#L274>
    """
    abi = Contract._load_abi(__name__, 'abi/GemJoin5.abi')
    bin = Contract._load_bin(__name__, 'abi/GemJoin5.bin')

    def __init__(self, web3: Web3, address: Address):
        super(GemJoin5, self).__init__(web3, address)
        self._token = self.gem()

    def dec(self) -> int:
        return int(self._contract.functions.dec().call())

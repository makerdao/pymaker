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

from typing import Optional

from web3 import Web3

from keeper.api import Contract, Address, Receipt, Transact
from keeper.api.util import bytes_to_hexstring, int_to_bytes32


class DSGuard(Contract):
    """A client for the `DSGuard` contract.

    You can find the source code of the `DSGuard` contract here:
    <https://github.com/dapphub/ds-guard>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSGuard` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSGuard.abi')
    bin = Contract._load_bin(__name__, 'abi/DSGuard.bin')

    ANY = int_to_bytes32(2 ** 256 - 1)

    def __init__(self, web3, address):
        self.web3 = web3
        self.address = address
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    @staticmethod
    def deploy(web3: Web3):
        return DSGuard(web3=web3, address=Contract._deploy(web3, DSGuard.abi, DSGuard.bin, []))

    def permit(self, src, dst, sig: bytes) -> Transact:
        assert(isinstance(src, Address) or isinstance(src, bytes))
        assert(isinstance(dst, Address) or isinstance(dst, bytes))
        assert(isinstance(sig, bytes) and len(sig) == 32)

        if isinstance(src, Address):
            src = src.address
        if isinstance(dst, Address):
            dst = dst.address

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'permit', [src, dst, sig])

    def forbid(self, src: Address, dst: Address, sig: bytes) -> Transact:
        assert(isinstance(src, Address) or isinstance(src, bytes))
        assert(isinstance(dst, Address) or isinstance(dst, bytes))
        assert(isinstance(sig, bytes) and len(sig) == 32)

        if isinstance(src, Address):
            src = src.address
        if isinstance(dst, Address):
            dst = dst.address

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'forbid', [src, dst, sig])

    def __repr__(self):
        return f"DSGuard('{self.address}')"


class DSRoles(Contract):
    """A client for the `DSRoles` contract.

    You can find the source code of the `DSRoles` contract here:
    <https://github.com/dapphub/ds-roles>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSRoles` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSRoles.abi')
    bin = Contract._load_bin(__name__, 'abi/DSRoles.bin')

    def __init__(self, web3, address):
        self.web3 = web3
        self.address = address
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    @staticmethod
    def deploy(web3: Web3):
        return DSRoles(web3=web3, address=Contract._deploy(web3, DSRoles.abi, DSRoles.bin, []))

    def __repr__(self):
        return f"DSRoles('{self.address}')"

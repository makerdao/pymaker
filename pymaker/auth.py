# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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

from pymaker import Contract, Address, Transact
from pymaker.util import int_to_bytes32


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

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3):
        return DSGuard(web3=web3, address=Contract._deploy(web3, DSGuard.abi, DSGuard.bin, []))

    def permit(self, src, dst, sig: bytes) -> Transact:
        """Grant access to a function call.

        Args:
            src: Address of the caller, or `ANY`.
            dst: Address of the called contract, or `ANY`.
            sig: Signature of the called function, or `ANY`.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(src, Address) or isinstance(src, bytes))
        assert(isinstance(dst, Address) or isinstance(dst, bytes))
        assert(isinstance(sig, bytes) and len(sig) in (4, 32))

        if isinstance(src, Address) and isinstance(dst, Address):
            method = 'permit(address,address,bytes32)'
            src = src.address
            dst = dst.address

        else:
            method = 'permit(bytes32,bytes32,bytes32)'

        return Transact(self, self.web3, self.abi, self.address, self._contract, method, [src, dst, sig])

    def __repr__(self):
        return f"DSGuard('{self.address}')"


# TODO: Complete implementation and unit test
class DSAuth(Contract):

    abi = Contract._load_abi(__name__, 'abi/DSAuth.abi')
    bin = Contract._load_bin(__name__, 'abi/DSAuth.bin')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3):
        return DSAuth(web3=web3, address=Contract._deploy(web3, DSAuth.abi, DSAuth.bin, []))

    def get_owner(self) -> Address:
        return Address(self._contract.call().owner())

    def set_owner(self, owner: Address) -> Transact:
        assert isinstance(owner, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        "setOwner", [owner.address])

    def set_authority(self, ds_authority: Address):
        assert isinstance(ds_authority, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        "setAuthority", [ds_authority.address])

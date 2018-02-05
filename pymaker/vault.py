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


class DSVault(Contract):
    """A client for the `DSVault` contract.

    You can find the source code of the `DSVault` contract here:
    <https://github.com/dapphub/ds-vault>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSVault` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSVault.abi')
    bin = Contract._load_bin(__name__, 'abi/DSVault.bin')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3):
        """Deploy a new instance of the `DSVault` contract.

        Args:
            web3: An instance of `Web` from `web3.py`.

        Returns:
            A `DSVault` class instance.
        """
        return DSVault(web3=web3, address=Contract._deploy(web3, DSVault.abi, DSVault.bin, []))

    def authority(self) -> Address:
        """Return the current `authority` of a `DSAuth`-ed contract.

        Returns:
            The address of the current `authority`.
        """
        return Address(self._contract.call().authority())

    def set_authority(self, address: Address) -> Transact:
        """Set the `authority` of a `DSAuth`-ed contract.

        Args:
            address: The address of the new `authority`.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(address, Address))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'setAuthority', [address.address])

    def __repr__(self):
        return f"DSVault('{self.address}')"

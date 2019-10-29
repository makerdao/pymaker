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


from pymaker import Address
from pymaker.numeric import Wad, Ray, Rad
from pymaker.shutdown import ShutdownModule
from pymaker.token import DSToken


def mint_mkr(mkr: DSToken, recipient_address: Address, amount: Wad):
    assert isinstance(mkr, DSToken)
    assert isinstance(recipient_address, Address)
    assert isinstance(amount, Wad)
    assert amount > Wad(0)

    deployment_address = Address("0x00a329c0648769A73afAc7F9381E08FB43dBEA72")
    assert mkr.mint(amount).transact(from_address=deployment_address)
    assert mkr.balance_of(deployment_address) > Wad(0)
    assert mkr.approve(recipient_address).transact(from_address=deployment_address)
    assert mkr.transfer(recipient_address, amount).transact(from_address=deployment_address)


class TestShutdownModule:
    """This test must be run after other MCD tests because it will leave the testchain `cage`d."""

    def test_init(self, mcd):
        assert mcd.esm is not None
        assert isinstance(mcd.esm, ShutdownModule)
        assert isinstance(mcd.esm.address, Address)
        assert(mcd.esm.sum() == Wad(0))
        assert(mcd.esm.min() > Wad(0))
        assert(not mcd.esm.fired())

    def test_join(self, mcd, our_address):
        assert mcd.mkr.approve(mcd.esm.address).transact()

        # This should have no effect yet succeed regardless
        assert mcd.esm.join(Wad(0)).transact()
        assert(mcd.esm.sum() == Wad(0))
        assert(mcd.esm.sum_of(our_address) == Wad(0))

        # Ensure the appropriate amount of MKR can be joined
        mint_mkr(mcd.mkr, our_address, mcd.esm.min())
        assert mcd.esm.join(mcd.esm.min()).transact()
        assert(mcd.esm.sum() == mcd.esm.min())

        # Joining extra MKR should succeed yet have no effect
        mint_mkr(mcd.mkr, our_address, Wad(153))
        assert mcd.esm.join(Wad(153)).transact()
        assert(mcd.esm.sum() == mcd.esm.min() + Wad(153))
        assert(mcd.esm.sum_of(our_address) == mcd.esm.sum())

    def test_fire(self, mcd):
        assert mcd.esm.fire().transact()
        assert(mcd.esm.fired())

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

import asyncio
import pytest
from mock import MagicMock
from web3 import Web3, HTTPProvider

from pymaker import Address, eth_transfer, TransactStatus, Calldata
from pymaker.gas import FixedGasPrice
from pymaker.numeric import Wad
from pymaker.proxy import DSProxy, DSProxyCache
from pymaker.token import DSToken
from pymaker.util import synchronize, eth_balance


class TestTransact:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.second_address = Address(self.web3.eth.accounts[1])
        self.third_address = Address(self.web3.eth.accounts[2])
        self.token = DSToken.deploy(self.web3, 'ABC')
        self.token.mint(Wad(1000000)).transact()

    def test_can_only_execute_once(self):
        # given
        transact = self.token.transfer(self.second_address, Wad(500))
        # and
        transact.transact()

        # expect
        with pytest.raises(Exception):
            transact.transact()

    def test_can_only_execute_once_even_if_tx_failed(self):
        # given
        transact = self.token.transfer(self.second_address, Wad(2000000))  # more than we minted
        # and
        try:
            transact.transact()
        # CAUTION: Note ganache 6.5+ causes a ValueError while older versions fail without exception
        except ValueError:
            pass

        # expect
        with pytest.raises(Exception):
            transact.transact()

    def test_should_update_status_when_finished(self):
        # given
        transact = self.token.transfer(self.second_address, Wad(500))
        assert transact.status == TransactStatus.NEW

        # when
        transact.transact()
        # then
        assert transact.status == TransactStatus.FINISHED

    def test_should_update_status_to_finished_even_if_tx_failed(self):
        # given
        transact = self.token.transfer(self.second_address, Wad(2000000))  # more than we minted
        assert transact.status == TransactStatus.NEW

        # when
        try:
            transact.transact()
        except ValueError:
            pass
        # then
        assert transact.status == TransactStatus.FINISHED

    def test_default_gas(self):
        # when
        receipt = self.token.transfer(self.second_address, Wad(500)).transact()

        # then
        assert 100000 <= self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] <= 1200000

    def test_default_gas_async(self):
        # when
        receipt = synchronize([self.token.transfer(self.second_address, Wad(500)).transact_async()])[0]

        # then
        assert 100000 <= self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] <= 1200000

    def test_custom_gas(self):
        # when
        receipt = self.token.transfer(self.second_address, Wad(500)).transact(gas=129995)

        # then
        assert self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] == 129995

    def test_custom_gas_async(self):
        # when
        receipt = synchronize([self.token.transfer(self.second_address, Wad(500)).transact_async(gas=129995)])[0]

        # then
        assert self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] == 129995

    def test_custom_gas_buffer(self):
        # when
        receipt = self.token.transfer(self.second_address, Wad(500)).transact(gas_buffer=2500000)

        # then
        assert self.web3.eth.getTransaction(receipt.transaction_hash)['gas'] > 2500000

    def test_gas_and_gas_buffer_not_allowed_at_the_same_time(self):
        # expect
        with pytest.raises(Exception):
            self.token.transfer(self.second_address, Wad(500)).transact(gas=129995, gas_buffer=3000000)

    def test_gas_and_gas_buffer_not_allowed_at_the_same_time_async(self):
        # expect
        with pytest.raises(Exception):
            synchronize([self.token.transfer(self.second_address, Wad(500)).transact_async(gas=129995,
                                                                                           gas_buffer=3000000)])

    def test_custom_gas_price(self):
        # given
        gas_price = FixedGasPrice(25000000100)

        # when
        self.token.transfer(self.second_address, Wad(500)).transact(gas_price=gas_price)

        # then
        assert self.web3.eth.getBlock('latest', full_transactions=True).transactions[0].gasPrice == gas_price.gas_price

    def test_custom_gas_price_async(self):
        # given
        gas_price = FixedGasPrice(25000000200)

        # when
        synchronize([self.token.transfer(self.second_address, Wad(500)).transact_async(gas_price=gas_price)])

        # then
        assert self.web3.eth.getBlock('latest', full_transactions=True).transactions[0].gasPrice == gas_price.gas_price

    def test_custom_from_address(self):
        # given
        self.token.transfer(self.second_address, Wad(self.token.balance_of(self.our_address))).transact()

        # when
        receipt = self.token.transfer(self.our_address, Wad(250)).transact(from_address=self.second_address)

        # then
        assert Address(self.web3.eth.getTransaction(receipt.transaction_hash)['from']) == self.second_address

    def test_name_formatting(self):
        # given
        transact = self.token.transfer(self.second_address, Wad(123))

        # expect
        assert transact.name() == f"DSToken('{self.token.address}').transfer('{self.second_address}', 123)"

    def test_name_formatting_with_hexstrings(self):
        # given
        proxy_cache = DSProxyCache.deploy(self.web3)
        proxy = DSProxy.deploy(self.web3, proxy_cache.address)

        # when
        transact = proxy.execute("0x11223344", Calldata("0x55667788"))

        # then
        assert transact.name() == f"DSProxy('{proxy.address}').execute(bytes,bytes)('0x11223344', '0x55667788')"

    def test_eth_transfer(self):
        # given
        initial_balance = eth_balance(self.web3, self.second_address)

        # when
        eth_transfer(self.web3, self.second_address, Wad.from_number(1.5)).transact()

        # then
        assert eth_balance(self.web3, self.second_address) == initial_balance + Wad.from_number(1.5)

    def test_eth_transfer_from_other_account(self):
        # given
        initial_balance_second_address = eth_balance(self.web3, self.second_address)
        initial_balance_third_address = eth_balance(self.web3, self.third_address)

        # when
        eth_transfer(self.web3, self.third_address, Wad.from_number(1.5)).transact(from_address=self.second_address)

        # then
        assert eth_balance(self.web3, self.second_address) < initial_balance_second_address
        assert eth_balance(self.web3, self.third_address) == initial_balance_third_address + Wad.from_number(1.5)

    def test_should_raise_exception_on_unknown_kwarg(self):
        # expect
        with pytest.raises(Exception):
            self.token.transfer(self.second_address, Wad(123)).transact(unknown_kwarg="some_value")

        # expect
        with pytest.raises(Exception):
            synchronize([self.token.transfer(self.second_address, Wad(123)).transact_async(unknown_kwarg="some_value")])


class TestTransactReplace:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.second_address = Address(self.web3.eth.accounts[1])
        self.third_address = Address(self.web3.eth.accounts[2])
        self.token = DSToken.deploy(self.web3, 'ABC')
        self.token.mint(Wad(1000000)).transact()

    @pytest.mark.asyncio
    async def test_transaction_replace(self):
        # given
        original_send_transaction = self.web3.eth.sendTransaction
        original_get_transaction = self.web3.eth.getTransaction
        nonce = self.web3.eth.getTransactionCount(self.our_address.address)

        # when
        self.web3.eth.sendTransaction = MagicMock(return_value='0xaaaaaaaaaabbbbbbbbbbccccccccccdddddddddd')
        self.web3.eth.getTransaction = MagicMock(return_value={'nonce': nonce})
        # and
        transact_1 = self.token.transfer(self.second_address, Wad(500))
        future_receipt_1 = asyncio.ensure_future(transact_1.transact_async())
        # and
        await asyncio.sleep(2)
        # then
        assert future_receipt_1.done() is False
        assert self.token.balance_of(self.second_address) == Wad(0)

        # when
        self.web3.eth.sendTransaction = original_send_transaction
        self.web3.eth.getTransaction = original_get_transaction
        # and
        transact_2 = self.token.transfer(self.third_address, Wad(700))
        future_receipt_2 = asyncio.ensure_future(transact_2.transact_async(replace=transact_1))
        # and
        await asyncio.sleep(10)
        # then
        assert transact_1.status == TransactStatus.FINISHED
        assert future_receipt_1.done()
        assert future_receipt_1.result() is None
        # and
        assert transact_2.status == TransactStatus.FINISHED
        assert future_receipt_2.done()
        assert future_receipt_2.result() is not None
        assert future_receipt_2.result().successful is True
        # and
        assert self.token.balance_of(self.second_address) == Wad(0)
        assert self.token.balance_of(self.third_address) == Wad(700)

    @pytest.mark.timeout(10)
    def test_transaction_replace_of_failed_transaction(self):
        # given
        original_send_transaction = self.web3.eth.sendTransaction

        # when
        transact_1 = self.token.transfer(self.second_address, Wad(2000000))  # more than we minted
        receipt_1 = None
        try:
            receipt_1 = transact_1.transact()
        except ValueError:
            pass
        # then
        assert transact_1.status == TransactStatus.FINISHED
        assert receipt_1 is None

        # when
        def second_send_transaction(transaction):
            # TestRPC doesn't support `sendTransaction` calls with the `nonce` parameter
            # (unlike proper Ethereum nodes which handle it very well)
            transaction_without_nonce = {key: transaction[key] for key in transaction if key != 'nonce'}
            return original_send_transaction(transaction_without_nonce)

        self.web3.eth.sendTransaction = MagicMock(side_effect=second_send_transaction)
        # when
        transact_2 = self.token.transfer(self.second_address, Wad(500))
        receipt_2 = transact_2.transact(replace=transact_1)
        # then
        assert transact_2.status == TransactStatus.FINISHED
        assert receipt_2 is not None
        assert receipt_2.successful
        # and
        assert self.token.balance_of(self.second_address) == Wad(500)

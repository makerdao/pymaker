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

import pytest
from hexbytes import HexBytes

from pymaker import Address, Calldata, Receipt, Transfer
from pymaker.numeric import Wad
from tests.helpers import is_hashable


class TestAddress:
    def test_creation_from_various_representations(self):
        # expect
        assert Address('0x0000000000111111111100000000001111111111').address == \
               '0x0000000000111111111100000000001111111111'
        assert Address('0000000000111111111100000000001111111111').address == \
               '0x0000000000111111111100000000001111111111'

    def test_creation_from_another_address(self):
        # given
        some_address = Address('0x0000000000111111111100000000001111111111')

        # expect
        assert Address(some_address).address == some_address.address

    def test_should_fail_creation_from_invalid_representation(self):
        # expect
        with pytest.raises(Exception):
            Address('0x000000000011111111110000000000111111111')  # too short

        # expect
        with pytest.raises(Exception):
            Address('0x00000000001111111111000000000011111111111')  # too long

    def test_as_bytes(self):
        # expect
        assert Address('0x0000011111000001111100000111110000011111').as_bytes() == \
               b'\0\0\x01\x11\x11\0\0\x01\x11\x11\0\0\x01\x11\x11\0\0\x01\x11\x11'

    def test_string_value(self):
        # expect
        assert str(Address('0x0000011111000001111100000111110000011111')) == \
               '0x0000011111000001111100000111110000011111'

    def test_repr(self):
        # expect
        assert repr(Address('0x0000011111000001111100000111110000011111')) == \
               "Address('0x0000011111000001111100000111110000011111')"

    def test_should_be_hashable(self):
        assert is_hashable(Address('0x0000011111000001111100000111110000011111'))

    def test_equality(self):
        # given
        address1a = Address('0x0000011111000001111100000111110000011111')
        address1b = Address('0x0000011111000001111100000111110000011111')
        address2 = Address('0x0000011111000001111100000111110000022222')

        # expect
        assert address1a == address1b
        assert address1a != address2
        assert address1b != address2

    def test_ordering(self):
        # given
        address1 = Address('0x0000011111000001111100000111110000011111')
        address2 = Address('0x0000011111000001111100000111110000022222')
        address3 = Address('0x0000011111000001111100000111110000033333')

        # expect
        assert address1 < address2
        assert not address1 > address2
        assert address2 > address1
        assert not address2 < address1
        assert address1 <= address2
        assert address2 >= address1
        assert address1 < address3
        assert address1 <= address3


class TestCalldata:
    def test_creation(self):
        # expect
        assert Calldata('0xa9059cbb').value == '0xa9059cbb'

    def test_creation_from_bytes(self):
        # expect
        assert Calldata(b'\xa9\x05\x9c\xbb').value == '0xa9059cbb'

    def test_should_fail_creation_from_invalid_calldata(self):
        # expect
        with pytest.raises(Exception):
            Calldata('a9059cbb')  # without `0x`

    def test_as_bytes(self):
        # expect
        assert Calldata('0xa9059cbb').as_bytes() == b'\xa9\x05\x9c\xbb'

    def test_string_value(self):
        # expect
        assert str(Calldata('0xa9059cbb')) == '0xa9059cbb'

    def test_repr(self):
        # expect
        assert repr(Calldata('0xa9059cbb')) == "Calldata('0xa9059cbb')"

    def test_should_be_hashable(self):
        assert is_hashable(Calldata('0xa9059cbb'))

    def test_equality(self):
        # given
        calldata1a = Calldata('0xa9059cbb')
        calldata1b = Calldata('0xa9059cbb')
        calldata2 = Calldata('0xa9059ccc')

        # expect
        assert calldata1a == calldata1b
        assert calldata1a != calldata2
        assert calldata1b != calldata2

    def test_from_signature(self):
        # given
        calldata1a = Calldata('0xa9059cbb'  # function 4byte signature
                              '00000000000000000000000011223344556600000000000000000000000000ff'
                              '000000000000000000000000000000000000000000000000000000000000007b')
        calldata1b = Calldata.from_signature('transfer(address,uint256)',
                                             ['0x11223344556600000000000000000000000000ff', 123])

        # expect
        assert calldata1a == calldata1b

        # given
        calldata2a = Calldata('0x2b4e4e96'  # function 4byte signature
                              '00000000000000000000000011223344556600000000000000000000000000ff'
                              '0000000000000000000000000000000000000000000000000000000000000040'
                              '0000000000000000000000000000000000000000000000000000000000000002'
                              '000000000000000000000000000000000000000000000000000000000000007b'
                              '00000000000000000000000000000000000000000000000000000000000001c8')
        calldata2b = Calldata.from_signature('transfer(address,uint256[])',
                                             ['0x11223344556600000000000000000000000000ff', [123, 456]])

        # expect
        assert calldata2a == calldata2b

class TestReceipt:
    @pytest.fixture()
    def receipt_success(self) -> dict:
        return {'blockHash': '0xef523d31d16592a53826962962bd126d1c66203780a2db59839eee3d3ff7d0b7',
                'blockNumber': 3890533,
                'contractAddress': None,
                'cumulativeGasUsed': 57192,
                'gasUsed': 57192,
                'logs': [{'address': '0x53eccc9246c1e537d79199d0c7231e425a40f896',
                          'blockHash': '0xef523d31d16592a53826962962bd126d1c66203780a2db59839eee3d3ff7d0b7',
                          'blockNumber': 3890533,
                          'data': '0x0000000000000000000000000000000000000000000000000de0b6b3a7640000',
                          'logIndex': 0,
                          'topics': [HexBytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
                                     HexBytes('0x000000000000000000000000375d52588c3f39ee7710290237a95c691d8432e7'),
                                     HexBytes('0x0000000000000000000000000046f01ad360270605e0e5d693484ec3bfe43ba8')],
                          'transactionHash': '0x8b6851e40d017b2004a54eae3e9e47614398b54bbbaae150eaa889ec36470ec8',
                          'transactionIndex': 0,
                          'transactionLogIndex': '0x0',
                          'type': 'mined'},
                         {'address': '0x375d52588c3f39ee7710290237a95c691d8432e7',
                          'blockHash': '0xef523d31d16592a53826962962bd126d1c66203780a2db59839eee3d3ff7d0b7',
                          'blockNumber': 3890533,
                          'data': '0x00000000000000000000000000000000000000000000000000000000000000a2',
                          'logIndex': 1,
                          'topics': [HexBytes('0xa2c251311b1a7a475913900a2a73dc9789a21b04bc737e050bbc506dd4eb3488')],
                          'transactionHash': '0x8b6851e40d017b2004a54eae3e9e47614398b54bbbaae150eaa889ec36470ec8',
                          'transactionIndex': 0,
                          'transactionLogIndex': '0x1',
                          'type': 'mined'},
                         {'address': '0x375d52588c3f39ee7710290237a95c691d8432e7',
                          'blockHash': '0xef523d31d16592a53826962962bd126d1c66203780a2db59839eee3d3ff7d0b7',
                          'blockNumber': 3890533,
                          'data': '0x00000000000000000000000053eccc9246c1e537d79199d0c7231e425a40f896000000000000000000000000228bf3d5be3ee4b80718b89b68069b023c32131e0000000000000000000000000000000000000000000000000de0b6b3a764000000000000000000000000000000000000000000000000000f6d7ac92d746b00000000000000000000000000000000000000000000000000000000000059c17c9c',
                          'logIndex': 2,
                          'topics': [HexBytes('0x9577941d28fff863bfbee4694a6a4a56fb09e169619189d2eaa750b5b4819995'),
                                     HexBytes('0x00000000000000000000000000000000000000000000000000000000000000a2'),
                                     HexBytes('0x7188d03e276d4dead4b0c037a93892d986e043a3af3305d7488a731ccaff4b76'),
                                     HexBytes('0x0000000000000000000000000046f01ad360270605e0e5d693484ec3bfe43ba8')],
                          'transactionHash': '0x8b6851e40d017b2004a54eae3e9e47614398b54bbbaae150eaa889ec36470ec8',
                          'transactionIndex': 0,
                          'transactionLogIndex': '0x2',
                          'type': 'mined'}],
                'logsBloom': '0x00000000000000000000000000000000000000000000002002000000000080000000000000800010000000000000000000000000000000000000000000000000000000000000000000000008000020000000000000000000000000040040000000000000000000100000000000000000000000000000000000000030000000000400000000000000000000000400000000000000000000000000000000000040001040000000000000000000000001000400000000000000000000002000000000000002000000100800000000080000080000000100000000000000000000002000000000000000000000000000000000000000000000000000000000000000',
                'root': None,
                'transactionHash': '0x8b6851e40d017b2004a54eae3e9e47614398b54bbbaae150eaa889ec36470ec8',
                'transactionIndex': 0}

    @pytest.fixture()
    def receipt_failed(self) -> dict:
        return {'blockHash': '0x827e0e913f4388318d5c08eff06e200ed1be1cb8b31aa30f932dcf5595c8d81d',
                'blockNumber': 3890936,
                'contractAddress': None,
                'cumulativeGasUsed': 3171658,
                'gasUsed': 3100000,
                'logs': [],
                'logsBloom': '0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
                'root': None,
                'transactionHash': '0x570369e4f70df947e3c4bc08ed9b06c181190a423ee5fcf17db203574e2d5d77',
                'transactionIndex': 1}

    def test_parsing_receipt(self, receipt_success):
        # given
        receipt = Receipt(receipt_success)

        # expect
        assert receipt.transaction_hash == '0x8b6851e40d017b2004a54eae3e9e47614398b54bbbaae150eaa889ec36470ec8'
        assert receipt.gas_used == 57192
        assert len(receipt.transfers) == 1
        assert len(receipt.logs) == 3
        assert receipt.transfers[0] == Transfer(token_address=Address('0x53eccc9246c1e537d79199d0c7231e425a40f896'),
                                                from_address=Address('0x375d52588c3f39ee7710290237a95c691d8432e7'),
                                                to_address=Address('0x0046f01ad360270605e0e5d693484ec3bfe43ba8'),
                                                value=Wad.from_number(1))

    def test_should_recognize_successful_and_failed_transactions(self, receipt_success, receipt_failed):
        # expect
        assert Receipt(receipt_success).successful is True
        assert Receipt(receipt_failed).successful is False


class TestTransfer:
    def test_equality(self):
        # given
        transfer1a = Transfer(token_address=Address('0x0000011111222223333344444555556666677777'),
                              from_address=Address('0x0000000000111111111100000000001111111111'),
                              to_address=Address('0x1111111111000000000011111111110000000000'),
                              value=Wad.from_number(20))
        transfer1b = Transfer(token_address=Address('0x0000011111222223333344444555556666677777'),
                              from_address=Address('0x0000000000111111111100000000001111111111'),
                              to_address=Address('0x1111111111000000000011111111110000000000'),
                              value=Wad.from_number(20))
        transfer2 = Transfer(token_address=Address('0x0000011111222223333344444555556666677777'),
                             from_address=Address('0x0000000000111111111100000000001111111111'),
                             to_address=Address('0x1111111111000000000011111111112222222222'),
                             value=Wad.from_number(20))

        # expect
        assert transfer1a == transfer1b
        assert transfer1b == transfer1a
        assert transfer1a != transfer2
        assert transfer1b != transfer2
        assert transfer2 != transfer1a
        assert transfer2 != transfer1b

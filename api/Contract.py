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

import json
import time

import pkg_resources
from web3.utils.events import get_event_data

from api.Address import Address
from api.Receipt import Receipt
from api.Transfer import Transfer
from api.Wad import Wad


class Contract:

    def _assert_contract_exists(self, web3, address):
        code = web3.eth.getCode(address.address)
        if (code == "0x") or (code is None):
            raise Exception(f"No contract found at {address}")

    def _wait_for_receipt(self, web3, transaction_hash):
        while True:
            receipt = web3.eth.getTransactionReceipt(transaction_hash)
            if receipt is not None and receipt['blockNumber'] is not None:
                return receipt
            time.sleep(0.25)

    def _prepare_receipt(self, web3, transaction_hash):
        receipt = self._wait_for_receipt(web3, transaction_hash)
        receipt_logs = receipt['logs']
        if (receipt_logs is not None) and (len(receipt_logs) > 0):
            transfers = []
            for receipt_log in receipt_logs:
                if len(receipt_log['topics']) > 0 and receipt_log['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                    from api.token import ERC20Token
                    transfer_abi = [abi for abi in ERC20Token.abi if abi.get('name') == 'Transfer'][0]
                    event_data = get_event_data(transfer_abi, receipt_log)
                    transfers.append(Transfer(token_address=Address(event_data['address']),
                                              from_address=Address(event_data['args']['from']),
                                              to_address=Address(event_data['args']['to']),
                                              value=Wad(event_data['args']['value'])))
            return Receipt(transaction_hash=transaction_hash, transfers=transfers)
        else:
            return False

    @staticmethod
    def _to_bytes32(value):
        return value.to_bytes(32, byteorder='big')

    @staticmethod
    def _load_abi(package, resource):
        return json.loads(pkg_resources.resource_string(package, resource))

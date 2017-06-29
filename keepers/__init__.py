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

import argparse
import json

from web3 import Web3, HTTPProvider

from api.Address import Address
from api.token.ERC20Token import ERC20Token


class Keeper:
    def start(self):
        parser = argparse.ArgumentParser(description=f"{type(self).__name__} keeper")
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
        self.args(parser)
        self.arguments = parser.parse_args()
        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.web3.eth.defaultAccount = self.arguments.eth_from #TODO allow to use ETH_FROM env variable
        self.our_address = Address(self.arguments.eth_from)
        self.config = Config(self.web3)

        self.init()

        label = f"{type(self).__name__} keeper"

        print(f"")
        print(f"{label}")
        print(f"{'-' * len(label)}")
        print(f"")
        print(f"Keeper operating as {self.our_address}")
        print(f"")

        self.run()

    def args(self, parser: argparse.ArgumentParser):
        pass

    def init(self):
        raise NotImplementedError("Please implement the init() method")

    def run(self):
        raise NotImplementedError("Please implement the run() method")


class Config:
    def __init__(self, web3: Web3):
        with open('keepers/addresses.json') as data_file:
            self.network = self._network_name(web3)
            self.addresses = json.load(data_file)
        for key, value in self.addresses[self.network]["tokens"].items():
            ERC20Token.register_token(Address(value), key)

    def get_contract_address(self, name):
        return self.addresses[self.network]["contracts"][name]

    @staticmethod
    def _network_name(web3: Web3) -> str:
        block_0 = web3.eth.getBlock(0)['hash']
        if block_0 == "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3":
            block_1920000 = web3.eth.getBlock(1920000)['hash']
            if block_1920000 == "0x94365e3a8c0b35089c1d1195081fe7489b528a84b22199c916180db8b28ade7f":
                return "etclive"
            else:
                return "ethlive"
        elif block_0 == "0xa3c565fc15c7478862d50ccd6561e3c06b24cc509bf388941c25ea985ce32cb9":
            return "kovan"
        elif block_0 == "0x41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d":
            return "ropsten"
        elif block_0 == "0x0cd786a2425d16f152c658316c423e6ce1181e15c3295826d7c9904cba9ce303":
            return "morden"
        else:
            return "unknown"

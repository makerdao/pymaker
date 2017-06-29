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

from web3 import Web3, HTTPProvider

from api.Address import Address
from keepers.Config import Config


class Keeper:
    def start(self):
        parser = argparse.ArgumentParser(description=(__name__ + 'keeper.'))
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
        self.args(parser)
        self.arguments = parser.parse_args()
        self.config = Config()
        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.web3.eth.defaultAccount = self.arguments.eth_from #TODO allow to use ETH_FROM env variable
        self.our_address = Address(self.arguments.eth_from)

        self.init()

        label = f"{type(self).__name__} keeper"

        print(f"")
        print(f"{label}")
        print(f"{'-' * len(label)}")
        print(f"")
        print(f"Keeper operating as {self.our_address}")

        self.run()

    def args(self, parser: argparse.ArgumentParser):
        pass

    def init(self):
        raise NotImplementedError("Please implement the init() method")

    def run(self):
        raise NotImplementedError("Please implement the run() method")

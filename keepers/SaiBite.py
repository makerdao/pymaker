#!/usr/bin/env python3
#
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
import time

from web3 import HTTPProvider
from web3 import Web3

from api.Address import Address
from api.sai.Tub import Tub
from keepers.Config import Config
from keepers.Keeper import Keeper


class SaiBite(Keeper):
    def __init__(self):
        parser = argparse.ArgumentParser(description='SaiBite keeper. Bites unsafe cups.')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
        parser.add_argument("--frequency", help="Frequency of checking for unsafe cups (in seconds) (default: 5)", default=5, type=int)
        self.args = parser.parse_args()

        config = Config()

        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.args.rpc_host}:{self.args.rpc_port}"))
        self.web3.eth.defaultAccount = self.args.eth_from #TODO allow to use ETH_FROM env variable

        self.tub_address = Address(config.get_contract_address("saiTub"))
        self.tap_address = Address(config.get_contract_address("saiTap"))
        self.top_address = Address(config.get_contract_address("saiTop"))
        self.tub = Tub(web3=self.web3, address_tub=self.tub_address, address_tap=self.tap_address, address_top=self.top_address)

        self.run()

    def run(self):
        print(f"")
        print(f"SaiBite keeper")
        print(f"--------------")

        while True:
            print(f"")
            for cup_id in range(1, self.tub.cupi()+1):
                if not self.tub.safe(cup_id):
                    print(f"Cup {cup_id} is not safe, biting it")
                    if self.tub.bite(cup_id):
                        print(f"Cup {cup_id} has been successfully bitten")
                    else:
                        print(f"*** FAILED to bite cup {cup_id}")
                else:
                    print(f"Cup {cup_id} is safe")

            time.sleep(self.args.frequency)


if __name__ == '__main__':
    SaiBite()

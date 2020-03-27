# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2020 EdNoepel
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

import logging
import sys
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.lifecycle import Lifecycle
from pymaker.deployment import DssDeployment
from pymaker.keys import register_keys
from pymaker.numeric import Wad

logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.DEBUG)
# reduce logspew
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger("web3").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("requests").setLevel(logging.INFO)

endpoint_uri = f"https://localhost:8545"
web3 = Web3(HTTPProvider(endpoint_uri=endpoint_uri, request_kwargs={"timeout": 30}))
web3.eth.defaultAccount = sys.argv[1]   # ex: 0x0000000000000000000000000000000aBcdef123
register_keys(web3, [sys.argv[2]])      # ex: key_file=~keys/default-account.json,pass_file=~keys/default-account.pass

mcd = DssDeployment.from_node(web3)
our_address = Address(web3.eth.defaultAccount)

collateral = mcd.collaterals['ETH-A']
ilk = collateral.ilk
collateral.approve(our_address)

class TestApp:
    def __init__(self):
        self.amount = Wad(3)
        self.joined = Wad(0)

    def main(self):
        with Lifecycle(web3) as lifecycle:
            lifecycle.on_shutdown(self.on_shutdown)
            lifecycle.on_block(self.on_block)

    def on_block(self):
        logging.info(f"Found new block, joining {self.amount} {ilk.name}  to our urn")
        collateral.gem.deposit(self.amount).transact()
        assert collateral.adapter.join(our_address, self.amount).transact()
        self.joined += self.amount
        logging.info(f"Urn balance is {mcd.vat.gem(ilk, our_address)} {ilk.name}")

    def on_shutdown(self):
        if self.joined > Wad(0):
            logging.info(f"Exiting {self.joined} {ilk.name} from our urn")
            assert collateral.adapter.exit(our_address, self.joined).transact()


if __name__ == '__main__':
    TestApp().main()

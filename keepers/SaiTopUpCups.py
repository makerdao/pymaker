#!/usr/bin/env python3

import argparse

import time
from web3 import HTTPProvider
from web3 import Web3

from contracts.Address import Address
from contracts.DSValue import DSValue
from contracts.ERC20Token import ERC20Token
from contracts.Ray import Ray
from contracts.Wad import Wad
from contracts.sai.Tub import Tub
from keepers.Config import Config

parser = argparse.ArgumentParser(description='Sai cups top-up keeper. Locks additional collateral in cups if they gett close to liquidation threshold.')
parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
parser.add_argument("--frequency", help="Frequency of checking for unsafe cups (in seconds) (default: 60)", default=60, type=float)
parser.add_argument("--minimum-margin", help="Margin between the liquidation ratio and the top-up threshold", default=0.1, type=int)
parser.add_argument("--target-margin", help="Margin between the liquidation ratio and the top-up target", default=0.25, type=float)
args = parser.parse_args()

config = Config()

web3 = Web3(HTTPProvider(endpoint_uri=f"http://{args.rpc_host}:{args.rpc_port}"))
web3.eth.defaultAccount = args.eth_from #TODO allow to use ETH_FROM env variable

tub_address = Address(config.get_contract_address("saiTub"))
tub = Tub(web3=web3, address=tub_address)

#TODO this is just some experimental code to test
# print(tub.air())
liquidation_ratio = tub.mat()
minimum_collateralization = liquidation_ratio + Ray.from_number(args.minimum_margin)
target_collateralization = liquidation_ratio + Ray.from_number(args.target_margin)

print(f"Liquidation ratio        : {liquidation_ratio}")
print(f"Minimum collateralization: {minimum_collateralization}")
print(f"Target collateralization : {target_collateralization}")
# print(tub.axe())
# print(tub.fix())
# print(tub.fog())
# print(tub.tag())
# print(tub.tip())
# print(tub.cups(1))
# print(tub.tab(1))

tip = DSValue(web3=web3, address=tub.tip())
# tip.watch()
# print(Wad(tip.read_as_int()))

skr = ERC20Token(web3=web3, address=tub.skr())
# print(skr.balance_of(Address(web3.eth.defaultAccount)))


# time.sleep(10000)
# time.sleep(1)
# time.sleep(1)
# time.sleep(1)

while True:
    for cup_id in range(1, tub.cupi()+1):
        #TODO as we do cups(...) and tab(...) in two separate calls, there is a slight chance that they might get evaulated
        #TODO on two different blocks, which will make the collateralization ratio calculation wrong
        cup = tub.cups(cup_id)
        if cup.lad == Address(web3.eth.defaultAccount):
            pro = cup.ink*tub.per()*tub.tag()
            tab = tub.tab(cup_id)
            current_collateralization = Ray.from_number(pro / tab)

            if current_collateralization < minimum_collateralization:
                top_up = Wad.from_number((target_collateralization - current_collateralization)*tab/(tub.per()*tub.tag()))
                print(f"Cup {cup_id} has collateralization ratio {current_collateralization} below {minimum_collateralization}")
                print(f"Cup {cup_id} needs top-up with {top_up} SKR so the collateralization ratio reaches {target_collateralization}")

                current_skr_allowance = skr.allowance_of(Address(web3.eth.defaultAccount), tub.address)

                if (current_skr_allowance < top_up):
                    print(f"Current SKR allowance is {current_skr_allowance} only, raising it")
                    if not skr.approve(tub.address, Wad(2**256-1)):
                        print("Approval failed!")
                        exit(-1)

                print(f"Topping up with {top_up} SKR")
                if not tub.lock(cup_id, top_up):
                    print("Top-up failed!")
                    exit(-1)

                print(f"Topped up with {top_up} SKR")
            else:
                print(
                    f"Cup {cup_id} has collateralization ratio {current_collateralization} above {minimum_collateralization}, ignoring")

    time.sleep(1)

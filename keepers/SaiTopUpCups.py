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

parser = argparse.ArgumentParser(description='SaiTopUpCups keeper. Locks additional collateral in cups if they get too close to the liquidation ratio.')
parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
parser.add_argument("--frequency", help="Frequency of checking for unsafe cups (in seconds) (default: 5)", default=5, type=float)
parser.add_argument("--minimum-margin", help="Margin between the liquidation ratio and the top-up threshold", default=0.1, type=int)
parser.add_argument("--target-margin", help="Margin between the liquidation ratio and the top-up target", default=0.25, type=float)
args = parser.parse_args()

config = Config()

web3 = Web3(HTTPProvider(endpoint_uri=f"http://{args.rpc_host}:{args.rpc_port}"))
web3.eth.defaultAccount = args.eth_from #TODO allow to use ETH_FROM env variable

our_address = Address(args.eth_from)
tub_address = Address(config.get_contract_address("saiTub"))
tub = Tub(web3=web3, address=tub_address)
tip = DSValue(web3=web3, address=tub.tip())
skr = ERC20Token(web3=web3, address=tub.skr())

liquidation_ratio = tub.mat()
minimum_ratio = liquidation_ratio + Ray.from_number(args.minimum_margin)
target_ratio = liquidation_ratio + Ray.from_number(args.target_margin)

print(f"")
print(f"SaiTopUpCups keeper")
print(f"-------------------")
print(f"Liquidation ratio: {liquidation_ratio}")
print(f"Minimum ratio    : {minimum_ratio}")
print(f"Target ratio     : {target_ratio}")
print(f"")

while True:
    for cup_id in range(1, tub.cupi()+1):
        #TODO as we do cups(...) and tab(...) in two separate calls, there is a slight chance that they might get evaulated
        #TODO on two different blocks, which will make the collateralization ratio calculation wrong
        cup = tub.cups(cup_id)
        if cup.lad == our_address:
            pro = cup.ink*tub.per()*tub.tag()
            tab = tub.tab(cup_id)
            current_ratio = Ray.from_number(pro / tab)

            if current_ratio < minimum_ratio:
                top_up_amount = Wad.from_number((target_ratio - current_ratio) * tab / (tub.per() * tub.tag()))
                print(f"Cup {cup_id} has collateralization ratio {current_ratio}, below {minimum_ratio}")
                print(f"Cup {cup_id} needs top-up with {top_up_amount} SKR so the collateralization ratio reaches {target_ratio}")

                skr_allowance = skr.allowance_of(our_address, tub.address)
                skr_balance = skr.balance_of(our_address)

                if skr_balance < top_up_amount:
                    print(f"Cannot perform the top-up as our balance is only {skr_balance} SKR, less than {top_up_amount} SKR")
                else:
                    if (skr_allowance < top_up_amount):
                        print(f"Current allowance is only {skr_allowance} SKR, which is less than {top_up_amount} SKR, raising it")
                        if not skr.approve(tub.address, Wad(2**256-1)):
                            print("*** FAILED to raise allowance, the top-up will probably fail as well!")

                    if tub.lock(cup_id, top_up_amount):
                        print(f"Cup {cup_id} has been topped up with {top_up_amount} SKR")
                    else:
                        print(f"*** FAILED to top-up cup {cup_id}!")
            else:
                print(
                    f"Cup {cup_id} has collateralization ratio {current_ratio}, above {minimum_ratio}, no need for top-up")

    time.sleep(args.frequency)

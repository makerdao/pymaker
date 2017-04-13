# create a new token and deploy it (use DSToken)
# test that it does sensible stuff


# TODO:
# scan through auction manager looking for new auctions
# i.e. reconstrut auction managers state

# reconstruct an individual auctions state (by scanning bid / split events)


# watch an auction manager for new auctions and do something


# watch an auction for new bids and do something, where something is
# probably a trading strategy



import json

from web3 import Web3
from web3 import EthereumTesterProvider

from contracts.DSToken import DSToken

web3 = Web3(EthereumTesterProvider())

with open('contracts/DSTokenBase.bin') as f:
    bytecode = f.read()

with open('contracts/DSTokenBase.abi') as f:
    abi = json.load(f)

Token = web3.eth.contract(abi=abi, bytecode=bytecode)
deploy = web3.eth.getTransactionReceipt(Token.deploy(kwargs={'supply': 1000000}))  # NOQA

token = DSToken(web3=web3, address=deploy['contractAddress'])

assert(token.total_supply() == 1000000)
assert(token.balance_of(web3.eth.accounts[0]) == 1000000)

token.transfer(web3.eth.accounts[1], 100)
token.transfer(web3.eth.accounts[1], 200)
token.transfer(web3.eth.accounts[2], 100)

# create a new token and deploy it (use DSTokenBase)

# test that it does sensible stuff

# include .sol assets with the package
import collections
import json

from web3 import Web3
from web3 import EthereumTesterProvider

web3 = Web3(EthereumTesterProvider())

with open('lib/ds-token/out/DSTokenBase.bin') as f:
    bytecode = f.read()

with open('lib/ds-token/out/DSTokenBase.abi') as f:
    abi = json.load(f)

Token = web3.eth.contract(abi=abi, bytecode=bytecode)
deploy = web3.eth.getTransactionReceipt(Token.deploy(kwargs={'supply': 1000000}))  # NOQA

token = Token(address=deploy['contractAddress'])

assert(token.call().totalSupply() == 1000000)
assert(token.call().balanceOf(web3.eth.accounts[0]) == 1000000)

token.transact().transfer(web3.eth.accounts[1], 100)
token.transact().transfer(web3.eth.accounts[1], 200)
token.transact().transfer(web3.eth.accounts[2], 100)

Market = web3.eth.contract(abi=abi, bytecode=bytecode)
Auction = web3.eth.contract(abi=abi, bytecode=bytecode)


class SimpleToken:
    def __init__(self, address):
        self.contract = Token(address=address)

        # {address => balance}
        self.state = collections.defaultdict(lambda: 0)
        #  reconstruction = self.reconstruct()
        #  reconstruction.join()
        #  self.watch({'fromBlock': self.contract.web3.eth.blockNumber})
        self.watch()

    def total_supply(self):
        return self.contract.call().totalSupply()

    def balance_of(self, address):
        return self.contract.call().balanceOf(address)

    def transfer(self, address, amount):
        return self.contract.transact().transfer(address, amount)

    def reconstruct(self, filter_params=None):
        """Scan over Transfer event history and determine the
        current token holdings."""
        return self.contract.pastEvents('Transfer', filter_params, self.update_balance)

    def watch(self, filter_params=None):
        return self.contract.on('Transfer', filter_params, self.update_balance)

    def update_balance(self, log):
        args = log['args']
        # state initialisation
        if not self.state:
            self.state[args['from']] = self.total_supply()

        self.state[args['from']] -= args['value']
        self.state[args['to']] += args['value']


class SimpleMarket:
    def __init__(self, address):
        self.contract = Market(address=address)

        self.state = {}

    def make(self, have_token, want_token, have_amount, want_amount):
        return self.contract.transact().make(have_token,
                                             want_token,
                                             have_amount,
                                             want_amount)

    def take(self, id, quantity):
        self.contract.transact().take(id, quantity)

    def kill(self, id):
        self.contact.transact().kill(id)

    def reconstruct(self):
        """Scan over the event history and determine the current
        state of the order book.
        """


class TokenAuction:
    def __init__(self, address):
        self.contract = Auction(address=address)

        self.state = {}

    def reconstruct(self):
        """Scan over the event history and determine the current
        state of the auction (following splits).
        """

    def bid(self, how_much, quantity):
        """
        """

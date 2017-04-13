import collections
import json


class DSToken:
    def __init__(self, web3, address):
        abi = self.__abi('contracts/DSToken.abi')
        self.contract = web3.eth.contract(abi=abi)(address=address)

        # {address => balance}
        self.state = collections.defaultdict(lambda: 0)
        #  reconstruction = self.reconstruct()
        #  reconstruction.join()
        #  self.watch({'fromBlock': self.contract.web3.eth.blockNumber})
        self.watch()

    def __abi(self, path):
        with open(path) as f:
            abi = json.load(f)
        return abi

    def total_supply(self):
        return self.contract.call().totalSupply()

    def balance_of(self, address):
        return self.contract.call().balanceOf(address)

    def transfer(self, address, amount):
        return self.contract.transact().transfer(address, amount)

    def reconstruct(self, filter_params=None):
        """Scan over Transfer event history and determine the
        current token holdings."""
        return self.contract.pastEvents('Transfer', filter_params, self.__update_balance)

    def watch(self, filter_params=None):
        return self.contract.on('Transfer', filter_params, self.__update_balance)

    def __update_balance(self, log):
        args = log['args']
        # state initialisation
        if not self.state:
            self.state[args['from']] = self.total_supply()

        self.state[args['from']] -= args['value']
        self.state[args['to']] += args['value']

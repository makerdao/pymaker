import collections

from contracts.Contract import Contract


class ERC20Token(Contract):
    def __init__(self, web3, address):
        self.web3 = web3
        self.address = address
        self.contract = web3.eth.contract(abi=self._load_abi('contracts/ERC20Token.abi'))(address=address.address)

        # {address => balance}
        self.state = collections.defaultdict(lambda: 0)
        self.watch()

    def total_supply(self):
        return self.contract.call().totalSupply()

    def balance_of(self, address):
        return self.contract.call().balanceOf(address)

    def allowance_of(self, address, payee):
        return self.contract.call().allowance(address, payee)

    def transfer(self, address, amount):
        return self.contract.transact().transfer(address, amount)

    def approve(self, address, limit):
        return self.contract.transact().approve(address, limit)

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

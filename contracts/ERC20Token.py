import collections

from contracts.Contract import Contract
from contracts.Wad import Wad


class ERC20Token(Contract):
    registry = {}

    def __init__(self, web3, address):
        self.address = address
        self._contract = web3.eth.contract(abi=self._load_abi(__name__, 'ERC20Token.abi'))(address=address.address)
        self._web3 = web3

        # {address => balance}
        self._state = collections.defaultdict(lambda: 0)
        self.watch()

    def name(self):
        return ERC20Token.registry.get(self.address, '???')

    def total_supply(self):
        return Wad(self._contract.call().totalSupply())

    def balance_of(self, address):
        return Wad(self._contract.call().balanceOf(address.address))

    def allowance_of(self, address, payee):
        return Wad(self._contract.call().allowance(address.address, payee.address))

    def transfer(self, address, amount):
        tx_hash = self._contract.transact().transfer(address.address, amount.value)
        return self._has_any_log_message(self._wait_for_receipt(tx_hash))

    def approve(self, address, limit):
        tx_hash = self._contract.transact().approve(address.address, limit.value)
        return self._has_any_log_message(self._wait_for_receipt(tx_hash))

    def reconstruct(self, filter_params=None):
        """Scan over Transfer event history and determine the
        current token holdings."""
        return self._contract.pastEvents('Transfer', filter_params, self.__update_balance)

    def watch(self, filter_params=None):
        return self._contract.on('Transfer', filter_params, self.__update_balance)

    def __update_balance(self, log):
        args = log['args']
        # state initialisation
        if not self._state:
            self._state[args['from']] = self.total_supply().value

        self._state[args['from']] -= args['value']
        self._state[args['to']] += args['value']

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"ERC20Token(address='{self.address}')"

    @staticmethod
    def register_token(address, name):
        ERC20Token.registry[address] = name

    @staticmethod
    def token_address_by_name(token_name):
        for address, name in ERC20Token.registry.items():
            if name == token_name:
                return address
        raise Exception(f"Token {token_name} not found")

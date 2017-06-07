import json

from contracts.Address import Address
from contracts.ERC20Token import ERC20Token


class Config:
    def __init__(self):
        with open('keepers/addresses.json') as data_file:
            self.network = "kovan" #TODO implement network detection
            self.addresses = json.load(data_file)
        for key, value in self.addresses[self.network]["tokens"].items():
            ERC20Token.register_token(Address(value), key)

    def get_contract_address(self, name):
        return self.addresses[self.network]["contracts"][name]

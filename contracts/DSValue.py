import json


class DSValue:
    def __init__(self, web3, address):
        abi = self.__abi('contracts/DSValue.abi')
        self.contract = web3.eth.contract(abi=abi)(address=address)

    def __abi(self, path):
        with open(path) as f:
            abi = json.load(f)
        return abi

    def has_value(self):
        return self.contract.call().peek()[1]

    def __get_value(self):
        return self.contract.call().peek()[0]

    def get_value_as_hex(self):
        return ''.join(hex(ord(x))[2:].zfill(2) for x in self.__get_value())

    def get_value_as_dec(self):
        return int(self.get_value_as_hex(), 16)

    # def set_value(self, xxx): TODO
    #     return self.contract.call().poke(xxx)

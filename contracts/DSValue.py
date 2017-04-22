from contracts.Contract import Contract


class DSValue(Contract):
    def __init__(self, web3, address):
        self.web3 = web3
        self.address = address
        self.contract = web3.eth.contract(abi=self._load_abi('contracts/DSValue.abi'))(address=address.address)

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

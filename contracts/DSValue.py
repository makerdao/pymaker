from contracts.Contract import Contract


class DSValue(Contract):
    def __init__(self, web3, address):
        self.web3 = web3
        self.address = address
        self.contract = web3.eth.contract(abi=self._load_abi(__name__, 'DSValue.abi'))(address=address.address)

    def has_value(self):
        return self.contract.call().peek()[1]

    def read(self):
        return self.contract.call().read()

    def read_as_hex(self):
        return ''.join(hex(ord(x))[2:].zfill(2) for x in self.read())

    def read_as_int(self):
        return int(self.read_as_hex(), 16)

    def watch(self):
        self.contract.on("LogNote", {'filter': {'sig': bytearray.fromhex('1504460f')}}, self.__note)
        self.contract.pastEvents("LogNote", {'fromBlock': 0, 'filter': {'sig': bytearray.fromhex('1504460f')}}, self.__note)

        # 'topics': ['0x1504460f00000000000000000000000000000000000000000000000000000000']
        # 'topics': ['0x1504460f00000000000000000000000000000000000000000000000000000000']

    def __note(self, log):
        print("AAA")
        args = log['args']
        print(args)




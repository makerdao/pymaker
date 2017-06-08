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

    def watch(self, filter_params=None):
        self.contract.on('LogNote', None, self.__note)
        self.contract.on('LogNote', {'fromBlock': 0}, self.__note)

    def __note(self, log):
        args = log['args']
        print(args)
        # # state initialisation
        # if not self._state:
        #     self._state[args['from']] = self.total_supply().value
        #
        # self._state[args['from']] -= args['value']
        # self._state[args['to']] += args['value']




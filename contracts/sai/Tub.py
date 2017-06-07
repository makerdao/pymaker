from contracts.Contract import Contract


class Tub(Contract):
    def __init__(self, web3, address):
        self.address = address
        self._contract = web3.eth.contract(abi=self._load_abi(__name__, 'Tub.abi'))(address=address.address)
        self._web3 = web3

    def cupi(self):
        return self._contract.call().cupi()

    def safe(self, cup_id):
        return self._contract.call().safe(self._to_bytes32(cup_id))

    def bite(self, cup_id):
        self._contract.transact().bite(self._to_bytes32(cup_id))

    def _to_bytes32(self, value):
        return value.to_bytes(32, byteorder='big')

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"Tub(address='{self.address}')"

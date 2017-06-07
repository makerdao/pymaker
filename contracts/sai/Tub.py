from contracts.Address import Address
from contracts.Contract import Contract
from contracts.Ray import Ray
from contracts.Wad import Wad


class Tub(Contract):
    def __init__(self, web3, address):
        self.address = address
        self._contract = web3.eth.contract(abi=self._load_abi(__name__, 'Tub.abi'))(address=address.address)
        self._web3 = web3

    """Get the amount of backing collateral"""
    def air(self):
        return Wad(self._contract.call().air())

    """Get the liquidation penalty"""
    def axe(self):
        return Ray(self._contract.call().axe())

    """Get the internal debt price"""
    def chi(self):
        return Ray(self._contract.call().chi())

    """Get the stability fee"""
    def tax(self):
        return Ray(self._contract.call().tax())

    """Get the SAI settlement price"""
    def fix(self):
        return Wad(self._contract.call().fix())

    """Get the amount of surplus sai"""
    def joy(self):
        return Wad(self._contract.call().joy())

    """Get the sai token"""
    def sai(self):
        return Address(self._contract.call().sai())

    """Get the sin token"""
    def sin(self):
        return Address(self._contract.call().sin())

    """Get the skr token"""
    def skr(self):
        return Address(self._contract.call().skr())

    """Get the amount of bad debt"""
    def woe(self):
        return Wad(self._contract.call().woe())

    """Get the amount of skr pending liquidation"""
    def fog(self):
        return Wad(self._contract.call().fog())

    """Get the reference price (ref per gem)"""
    def tag(self):
        return Wad(self._contract.call().tag())

    """Get the gem price feed"""
    def tip(self):
        return Address(self._contract.call().tip())

    """Get the last cup id"""
    def cupi(self):
        return self._contract.call().cupi()

    """Determine if a cup is safe"""
    def safe(self, cup_id):
        return self._contract.call().safe(self._to_bytes32(cup_id))

    """Initiate liquidation of an undercollateralized cup"""
    def bite(self, cup_id):
        self._contract.transact().bite(self._to_bytes32(cup_id))

    def _to_bytes32(self, value):
        return value.to_bytes(32, byteorder='big')

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"Tub(address='{self.address}')"

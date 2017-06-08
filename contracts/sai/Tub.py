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

    """Get the current entry price (gem per skr)"""
    def per(self):
        return Ray(self._contract.call().per())

    """Get the reference price (ref per gem)"""
    def tag(self):
        return Wad(self._contract.call().tag())

    """Get the liquidation ratio"""
    def mat(self):
        return Ray(self._contract.call().mat())

    """Get the gem price feed"""
    def tip(self):
        return Address(self._contract.call().tip())

    """Get the last cup id"""
    def cupi(self):
        return self._contract.call().cupi()

    """Get the cup details"""
    def cups(self, cup_id):
        assert isinstance(cup_id, int)
        array = self._contract.call().cups(self._to_bytes32(cup_id))
        return Cup(Address(array[0]), Wad(array[1]), Wad(array[2]))

    """Get how much debt in a cup"""
    def tab(self, cup_id):
        assert isinstance(cup_id, int)
        return Wad(self._contract.call().tab(self._to_bytes32(cup_id)))

    """Determine if a cup is safe"""
    def safe(self, cup_id):
        assert isinstance(cup_id, int)
        return self._contract.call().safe(self._to_bytes32(cup_id))

    """Post additional SKR collateral to a cup"""
    def lock(self, cup_id, amount_in_skr):
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_skr, Wad)
        tx_hash = self._contract.transact().lock(self._to_bytes32(cup_id), amount_in_skr.value)
        return self._has_any_log_message(self._wait_for_receipt(tx_hash))

    """Initiate liquidation of an undercollateralized cup"""
    def bite(self, cup_id):
        assert isinstance(cup_id, int)
        tx_hash = self._contract.transact().bite(self._to_bytes32(cup_id))
        return self._has_any_log_message(self._wait_for_receipt(tx_hash))

    """Buy some amount of sai to process joy (surplus)"""
    def boom(self, cup_id, amount_in_skr):
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_skr, Wad)
        tx_hash = self._contract.transact().boom(self._to_bytes32(cup_id), amount_in_skr.value)
        return self._has_any_log_message(self._wait_for_receipt(tx_hash))

    """Sell some amount of sai to process woe (bad debt)"""
    def bust(self, cup_id, amount_in_skr):
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_skr, Wad)
        tx_hash = self._contract.transact().bust(self._to_bytes32(cup_id), amount_in_skr.value)
        return self._has_any_log_message(self._wait_for_receipt(tx_hash))

    def _to_bytes32(self, value):
        return value.to_bytes(32, byteorder='big')

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"Tub(address='{self.address}')"


class Cup:
    def __init__(self, lad, art, ink):
        self.lad = lad
        self.art = art
        self.ink = ink

    def __repr__(self):
        return f"Cup(lad={repr(self.lad)}, art={self.art}, ink={self.ink})"

from contracts.Address import Address
from contracts.Contract import Contract
from contracts.Ray import Ray
from contracts.Wad import Wad


class Tub(Contract):
    abi = Contract._load_abi(__name__, 'Tub.abi')

    def __init__(self, web3, address):
        self._assert_contract_exists(web3, address)
        self.address = address
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)
        self._web3 = web3

    def air(self):
        """Get the amount of backing collateral"""
        return Wad(self._contract.call().air())

    def axe(self):
        """Get the liquidation penalty"""
        return Ray(self._contract.call().axe())

    def chi(self):
        """Get the internal debt price"""
        return Ray(self._contract.call().chi())

    def tax(self):
        """Get the stability fee"""
        return Ray(self._contract.call().tax())

    def rho(self):
        """Get the time of last drip"""
        return Ray(self._contract.call().tax())

    def fix(self):
        """Get the SAI settlement price"""
        return Wad(self._contract.call().fix())

    def joy(self):
        """Get the amount of surplus sai"""
        return Wad(self._contract.call().joy())

    def sai(self):
        """Get the sai token"""
        return Address(self._contract.call().sai())

    def sin(self):
        """Get the sin token"""
        return Address(self._contract.call().sin())

    def skr(self):
        """Get the skr token"""
        return Address(self._contract.call().skr())

    def woe(self):
        """Get the amount of bad debt"""
        return Wad(self._contract.call().woe())

    def fog(self):
        """Get the amount of skr pending liquidation"""
        return Wad(self._contract.call().fog())

    def per(self):
        """Get the current entry price (gem per skr)"""
        return Ray(self._contract.call().per())

    def tag(self):
        """Get the reference price (ref per gem)"""
        return Wad(self._contract.call().tag())

    def mat(self):
        """Get the liquidation ratio"""
        return Ray(self._contract.call().mat())

    def tip(self):
        """Get the gem price feed"""
        return Address(self._contract.call().tip())

    def cupi(self):
        """Get the last cup id"""
        return self._contract.call().cupi()

    def cups(self, cup_id):
        """Get the cup details"""
        assert isinstance(cup_id, int)
        array = self._contract.call().cups(self._to_bytes32(cup_id))
        return Cup(Address(array[0]), Wad(array[1]), Wad(array[2]))

    def tab(self, cup_id):
        """Get how much debt in a cup"""
        assert isinstance(cup_id, int)
        return Wad(self._contract.call().tab(self._to_bytes32(cup_id)))

    def safe(self, cup_id):
        """Determine if a cup is safe"""
        assert isinstance(cup_id, int)
        return self._contract.call().safe(self._to_bytes32(cup_id))

    def lock(self, cup_id, amount_in_skr):
        """Post additional SKR collateral to a cup"""
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_skr, Wad)
        tx_hash = self._contract.transact().lock(self._to_bytes32(cup_id), amount_in_skr.value)
        return self._prepare_receipt(self._wait_for_receipt(tx_hash))

    def bite(self, cup_id):
        """Initiate liquidation of an undercollateralized cup"""
        assert isinstance(cup_id, int)
        tx_hash = self._contract.transact().bite(self._to_bytes32(cup_id))
        return self._prepare_receipt(self._wait_for_receipt(tx_hash))

    def boom(self, amount_in_skr):
        """Buy some amount of sai to process joy (surplus)"""
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().boom(amount_in_skr.value)
            return self._prepare_receipt(self._wait_for_receipt(tx_hash))
        except:
            return False

    def bust(self, amount_in_skr):
        """Sell some amount of sai to process woe (bad debt)"""
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().bust(amount_in_skr.value)
            return self._prepare_receipt(self._wait_for_receipt(tx_hash))
        except:
            return False

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

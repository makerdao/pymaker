import eth_utils


class Address:
    def __init__(self, address):
        self.address = eth_utils.to_normalized_address(address)

    def __str__(self):
        return f"'${self.address}'"

    def __repr__(self):
        return f"Address('{self.address}')"

    def __eq__(self, other):
        return self.address == other.address
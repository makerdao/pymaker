import eth_utils


class Address:
    def __init__(self, address):
        if (isinstance(address, Address)):
            self.address = address.address
        else:
            self.address = eth_utils.to_normalized_address(address)

    def __str__(self):
        return f"{self.address}"

    def __repr__(self):
        return f"Address('{self.address}')"

    def __hash__(self):
        return self.address.__hash__()

    def __eq__(self, other):
        return self.address == other.address

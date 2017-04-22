class SimpleMarket:
    def __init__(self, web3, address):
        Market = web3.eth.contract(abi=abi, bytecode=bytecode)
        self.contract = Market(address=address)

        self.state = {}

    def make(self, have_token, want_token, have_amount, want_amount):
        return self.contract.transact().make(have_token,
                                             want_token,
                                             have_amount,
                                             want_amount)

    def take(self, id, quantity):
        self.contract.transact().take(id, quantity)

    def kill(self, id):
        self.contact.transact().kill(id)

    def reconstruct(self):
        """Scan over the event history and determine the current
        state of the order book.
        """

class TokenAuction:
    def __init__(self, address):
        Auction = web3.eth.contract(abi=abi, bytecode=bytecode)
        self.contract = Auction(address=address)

        self.state = {}

    def reconstruct(self):
        """Scan over the event history and determine the current
        state of the auction (following splits).
        """

    def bid(self, how_much, quantity):
        """
        """

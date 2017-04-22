from contracts.ERC20Token import ERC20Token


class DSToken(ERC20Token):
    def is_stopped(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def push(self, address, amount):
        raise NotImplementedError

    def pull(self, address, amount):
        raise NotImplementedError

    def mint(self, amount):
        raise NotImplementedError

    def burn(self, amount):
        raise NotImplementedError


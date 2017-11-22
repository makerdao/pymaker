# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from web3 import Web3

from keeper.api import Contract, Address


# class Order:
#     def __init__(self, token_get: Address, amount_get: Wad, token_give: Address, amount_give: Wad, expires: int,
#                  nonce: int, user: Address, v: int, r: bytes, s: bytes):
#         super().__init__(token_get, amount_get, token_give, amount_give, expires)
#
#         assert(isinstance(nonce, int))
#         assert(isinstance(user, Address))
#         assert(isinstance(v, int))
#         assert(isinstance(r, bytes))
#         assert(isinstance(s, bytes))
#
#         self.nonce = nonce
#         self.user = user
#         self.v = v
#         self.r = r
#         self.s = s
#
#     @property
#     def sell_how_much(self):
#         return self.amount_give
#
#     @property
#     def buy_how_much(self):
#         return self.amount_get
#
#     @staticmethod
#     def from_json(data: dict):
#         assert(isinstance(data, dict))
#         return OffChainOrder(token_get=Address(data['tokenGet']),
#                              amount_get=Wad(int(data['amountGet'])),
#                              token_give=Address(data['tokenGive']),
#                              amount_give=Wad(int(data['amountGive'])),
#                              expires=int(data['expires']),
#                              nonce=int(data['nonce']),
#                              v=int(data['v']),
#                              r=hexstring_to_bytes(data['r']),
#                              s=hexstring_to_bytes(data['s']),
#                              user=Address(data['user']))
#
#     def to_json(self, etherdelta_contract_address: Address) -> dict:
#         return {'contractAddr': etherdelta_contract_address.address,
#                 'tokenGet': self.token_get.address,
#                 'amountGet': self.amount_get.value,
#                 'tokenGive': self.token_give.address,
#                 'amountGive': self.amount_give.value,
#                 'expires': self.expires,
#                 'nonce': self.nonce,
#                 'v': self.v,
#                 'r': bytes_to_hexstring(self.r),
#                 's': bytes_to_hexstring(self.s),
#                 'user': self.user.address}
#
#     def __eq__(self, other):
#         if isinstance(other, OffChainOrder):
#             return self.token_get == other.token_get and \
#                    self.amount_get == other.amount_get and \
#                    self.token_give == other.token_give and \
#                    self.amount_give == other.amount_give and \
#                    self.expires == other.expires and \
#                    self.nonce == other.nonce and \
#                    self.user == other.user and \
#                    self.v == other.v and \
#                    self.r == other.r and \
#                    self.s == other.s
#         else:
#             return False
#
#     def __hash__(self):
#         return hash((self.token_get,
#                      self.amount_get,
#                      self.token_give,
#                      self.amount_give,
#                      self.expires,
#                      self.nonce,
#                      self.user,
#                      self.v,
#                      self.r,
#                      self.s))
#
#     def __str__(self):
#         return f"('{self.token_get}', '{self.amount_get}'," \
#                f" '{self.token_give}', '{self.amount_give}'," \
#                f" '{self.expires}', '{self.nonce}')"
#
#     def __repr__(self):
#         return pformat(vars(self))


class RadarRelay(Contract):
    """A client for the RadarRelay/0x exchange contract.

    You can find the source code of the `0x` exchange contract here:
    <https://etherscan.io/address/0x12459c951127e0c374ff9105dda097662a027093#code.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the _0x_ `Exchange` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/Exchange.abi')
    bin = Contract._load_bin(__name__, 'abi/Exchange.bin')

    @staticmethod
    def deploy(web3: Web3,
               zrx_token: Address,
               token_transfer_proxy: Address):
        """Deploy a new instance of the `EtherDelta` contract.

        Args:
            web3: An instance of `Web` from `web3.py`.

        Returns:
            A `RadarRelay` class instance.
        """
        return RadarRelay(web3=web3,
                          address=Contract._deploy(web3, RadarRelay.abi, RadarRelay.bin, [
                              zrx_token.address,
                              token_transfer_proxy.address
                          ]))

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def __repr__(self):
        return f"RadarRelay()"

from web3 import Web3
from web3 import HTTPProvider

from contracts.Address import Address
from contracts.DSValue import DSValue


web3 = Web3(HTTPProvider(endpoint_uri='http://localhost:8545'))

value1 = DSValue(web3, Address('0x965dd125dea8cd78821ca178e179b4c688042322'))
value2 = DSValue(web3, Address('0x8948974aec1f4092a0c772b69b5d9da9d073bcd2'))
value3 = DSValue(web3, Address('0x9b8b908a6eac509498b210bbcba00e45a6ce8f87'))

value_medianizer = DSValue(web3, Address('0x90c9804A397946B80FcCD66e86cE476A0Ffbec15'))


print(value1.has_value())
print(value2.has_value())
print(value3.has_value())
print(value_medianizer.has_value())

print(value1.read_as_int())
print(value2.read_as_int())
print(value3.read_as_int())
print(value_medianizer.read_as_int())


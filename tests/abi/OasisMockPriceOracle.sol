pragma solidity ^0.5.12;

contract OasisMockPriceOracle {
    uint256 price;
    function setPrice(address, uint256 _price) public {
        price = _price;
    }

    function getPriceFor(address, address, uint256) public view returns (uint256) {
        return price;
    }
}
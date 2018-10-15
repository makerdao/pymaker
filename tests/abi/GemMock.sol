pragma solidity ^0.4.24;

import "ds-token/token.sol";

contract GemMock is DSToken('') {

    constructor(bytes32 symbol_) public {
        symbol = symbol_;
    }

    function can(address src, address guy) public view returns (bool) {
        if (allowance(src, guy) > 0) {
            return true;
        }

        return false;
    }

    function push(bytes32 guy, uint wad) public { push(address(guy), wad); }
    function hope(address guy) public { approve(guy); }
    function nope(address guy) public { approve(guy, 0); }
}

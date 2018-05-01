pragma solidity ^0.4.23;

contract VatMock {

    mapping (address => int256) public dai;
    mapping (address => int256) public gem;

    // this is only a mock:
    // - everybody can mint
    // - no overflow/underflow protection
    // - `ilk` is permanently ignored

    function flux(bytes32 ilk, address lad, int wad) public {
        gem[lad] += wad;
    }

    function mint(address lad, uint256 wad) public {
        dai[lad] += int(wad);
    }

    function move(address src, address dst, uint256 wad) public {
        require(dai[src] >= int(wad));
        dai[src] -= int(wad);
        dai[dst] += int(wad);
    }

}

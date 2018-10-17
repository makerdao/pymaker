pragma solidity ^0.4.24;

// Fusion between a DaiJoin and a DaiMove

contract GemLike {
    function transferFrom(address,address,uint) public returns (bool);
    function mint(address,uint) public;
    function burn(address,uint) public;
}

contract VatLike {
    function slip(bytes32,bytes32,int) public;
    function move(bytes32,bytes32,int) public;
    function flux(bytes32,bytes32,bytes32,int) public;
}

contract DaiMock {
    VatLike public vat;
    GemLike public dai;
    constructor(address vat_, address dai_) public {
        vat = VatLike(vat_);
        dai = GemLike(dai_);
    }
    uint constant ONE = 10 ** 27;
    function mul(uint x, uint y) internal pure returns (int z) {
        z = int(x * y);
        require(int(z) >= 0);
        require(y == 0 || uint(z) / y == x);
    }
    mapping(address => mapping (address => bool)) public can;
    function hope(address guy) public { can[msg.sender][guy] = true; }
    function nope(address guy) public { can[msg.sender][guy] = false; }
    function move(address src, address dst, uint wad) public {
        require(src == msg.sender || can[src][msg.sender]);
        vat.move(bytes32(src), bytes32(dst), mul(ONE, wad));
    }
    function join(bytes32 urn, uint wad) public {
        vat.move(bytes32(address(this)), urn, mul(ONE, wad));
        dai.burn(msg.sender, wad);
    }
    function exit(address guy, uint wad) public {
        vat.move(bytes32(msg.sender), bytes32(address(this)), mul(ONE, wad));
        dai.mint(guy, wad);
    }
}

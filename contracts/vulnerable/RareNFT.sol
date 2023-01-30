//SPDX-License-Identifier: Unlicense
pragma solidity ^0.8.4;

import {Ownable} from "@openzeppelin/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/security/ReentrancyGuard.sol";
import "../tokens/MockERC721.sol";

contract RareNFT is Ownable, ReentrancyGuard {
    MockERC721 immutable nftContract;
    uint256 public nftPrice = 1 ether;
    uint256 private nonce;
    uint256 private luckyVal;

    struct Token {
        address owner;
        uint256 value;
        bool rare;
    }
    mapping(uint256 => Token) public tokenInfo;
    mapping(address => bool) public minted;
    mapping(address => bool) public collected;

    event NFTcontract(address nft);
    event PriceChanged(uint256 oldPrice, uint256 newPrice);
    event Minted(uint256 id, address owner);
    event Collected(uint256 id, address owner);

    constructor() payable {
        require(msg.value >= 1 ether, "RareNFT: requires 1 ether");
        luckyVal = _luckyValGenerator();
        MockERC721 _nftContract = new MockERC721();
        nftContract = _nftContract;
        emit NFTcontract(address(_nftContract));
    }

    function _luckyValGenerator() internal view returns (uint256) {
        uint256 num = uint256(keccak256(abi.encodePacked(block.difficulty, block.timestamp))) % 5;
        if (num == 0) {
            num++;
        }
        return num;
    }

    function changePrice(uint256 newPrice) external onlyOwner {
        require(newPrice > 0, "RareNFT: new price must be greater than 0");
        emit PriceChanged(nftPrice, newPrice);
        nftPrice = newPrice;
    }

    function changeLuckyVal(uint256 _luckyVal) external onlyOwner {
        require(_luckyVal > 0, "RareNFT: luckyVal must be greater than 0");
        luckyVal = _luckyVal;
    }

    function _randGenerator(uint256 _drawNum) internal returns (uint256) {
        require(_drawNum > 0, "RareNFT: drawNum must be greater than 0");
        bytes32 randHash = keccak256(
            abi.encodePacked(
                blockhash(block.number - 1),
                block.timestamp,
                block.coinbase,
                gasleft(),
                tx.gasprice,
                tx.origin,
                nonce,
                msg.sender
            )
        );
        uint256 random = uint256(randHash) % _drawNum;
        nonce++;
        return random;
    }

    function mint(uint256 drawNum) external payable nonReentrant {
        require(!minted[msg.sender], "RareNFT: you have already minted");
        require(msg.value == nftPrice, "RareNFT: requires mint amount");
        uint256 id = nftContract.mint();
        uint256 randVal = _randGenerator(drawNum);
        if (randVal == luckyVal) {
            tokenInfo[id] = Token({owner: msg.sender, value: nftPrice, rare: true});
        } else {
            tokenInfo[id] = Token({owner: msg.sender, value: nftPrice, rare: false});
        }
        minted[msg.sender] = true;
        emit Minted(id, msg.sender);
    }

    function collect(uint256 id) external payable nonReentrant {
        require(!collected[msg.sender], "RareNFT: you have already collected");
        Token memory tk = tokenInfo[id];
        require(nftContract.ownerOf(id) == msg.sender, "RareNFT: id doesn't belongs to you");
        if (tk.rare) {
            payable(msg.sender).transfer(0.1 ether);
        }
        nftContract.safeTransferFrom(address(this), msg.sender, id);
        collected[msg.sender] = true;
        emit Collected(id, msg.sender);
    }

    function get_nonce() public view returns (uint256) {
            return nonce;
        }
}

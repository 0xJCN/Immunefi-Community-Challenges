# @version^0.3.7

"""
Need to complete
"""

owner: immutable(address)

@external
@payable
def __init__():
    owner = msg.sender

@external
def attack():
    assert msg.sender == owner, "!owner"

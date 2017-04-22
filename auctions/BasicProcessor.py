from auctions.ActionBid import ActionBid
from auctions.ActionPass import ActionPass


class BasicProcessor:
    def __init__(self, strategy):
        self.strategy = strategy

    def process_auctionlet(self, auctionlet, our_buyer, auction_manager_address):
        auctionlet_info = auctionlet.get_info()
        auctionlet_expired = auctionlet.is_expired()

        # for expired&claimed auctionlets, these methods return None
        if (auctionlet_info is None) or (auctionlet_expired is None):
            return ProcessResult('Auctionlet is already gone. Removing.', forget_auctionlet=True)

        # get the base auction info
        auction = auctionlet.get_auction()
        auction_info = auction.get_info()

        if auctionlet.is_expired():
            if auctionlet_info.unclaimed and (auctionlet_info.last_bidder == our_buyer):
                claim_result = auctionlet.claim()
                if claim_result:
                    return ProcessResult(f"Expired, we won, claimed by us successfully.", forget_auctionlet=True)
                else:
                    return ProcessResult(f"Expired, we won, tried to claim it but it failed")
            else:
                return ProcessResult('Expired, waiting to be claimed by somebody else. Removing.', forget_auctionlet=True)
        else:
            if auctionlet_info.last_bidder == our_buyer:
                return ProcessResult('We are the highest bidder. Not doing anything.')
            else:
                action = self.strategy.action(auction_info, auctionlet_info, our_buyer, auction_manager_address)
                if isinstance(action, ActionBid):
                    bid_amount = action.bid_amount
                    bid_result = auctionlet.bid(bid_amount)

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

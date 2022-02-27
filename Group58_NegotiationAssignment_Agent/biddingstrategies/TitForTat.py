from decimal import Decimal
from queue import Queue
from random import randint

from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.bidspace.Interval import Interval
from geniusweb.issuevalue.Bid import Bid
from tudelft.utilities.immutablelist.ImmutableList import ImmutableList


class TitForTat:
    def __init__(self, profile, opponent_model, offer):
        self._profile = profile
        self.opponent_model = opponent_model
        self._offer = offer
        
       

    def find_offer(self, op_bids: Queue):
        # TODO remove assert statement.
        assert(op_bids.qsize() < 3)
        if op_bids.qsize() == 2:
            # Measure the difference between utilities of the last two opponent bids.
            # based on my utility function
            op_bid_old = op_bids.get()
            op_bid_new = op_bids.get()
            # put back the newest bid as oldest now
            op_bids.put(op_bid_new)

            op_bid_old_util = self._profile.getUtility(op_bid_old)
            op_bid_new_util = self._profile.getUtility(op_bid_new)
            util_diff = abs(op_bid_old_util - op_bid_new_util)
            
            if (util_diff > 0.1):
                util_diff = Decimal(0.1)

            if op_bid_new_util > op_bid_old_util:
                # if the new offer has higher util than before
                # opponent made a concession for my utility and we
                # are reciprocating by also making a concession

                print("conceded")
                self._offer = Decimal(self._offer) - util_diff #Decimal(0.05)
                return self._offer
        
        return Decimal(self._offer)

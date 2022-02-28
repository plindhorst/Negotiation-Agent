from decimal import Decimal
from queue import Queue

from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.bidspace.Interval import Interval
from geniusweb.issuevalue.Bid import Bid

from Group58_NegotiationAssignment_Agent.Constants import Constants

class TitForTat:
    def __init__(self, profile, opponent_model, offer):
        self._profile = profile
        self.opponent_model = opponent_model
        self._offer = offer
        self._bidUtils = BidsWithUtility.create(self._profile) 
    
    def find_bid(self, offer, op_bids: Queue, my_bid_last: Bid):
        self._offer = offer
        # Only apply strategy when there are more than 2 bids of opponent.
        if op_bids.qsize() == 2:
            # Measure the difference between utilities of the last two opponent bids.
            # based on my utility function
            op_bid_old = op_bids.get()
            op_bid_new = op_bids.get()
            # put back the newest bid as oldest now
            op_bids.put(op_bid_new)

            my_bid_last_util = self._profile.getUtility(my_bid_last)
            op_bid_old_util = self._profile.getUtility(op_bid_old)
            op_bid_new_util = self._profile.getUtility(op_bid_new)
            util_diff = abs(op_bid_old_util - op_bid_new_util) * Decimal(0.4)
            
            range = None
            if op_bid_new_util > op_bid_old_util:
                # if the new offer has higher util than before
                # opponent made a concession for my utility and we
                # are reciprocating by also making a concession
                range = Interval(
                    Decimal(self._offer) - util_diff,
                    Decimal(self._offer),
                )

                bids = self._bidUtils.getBids(range)
                # Prevent having empty bids list by expanding it slightly till we find bids
                if bids.size() == 0:
                    bids = self._bidUtils.getBids(Interval(
                    Decimal(self._offer - Constants.tft_max_concession),
                    Decimal(self._offer),
                ))

                # Find a bid that is best for the opponent using opponent model
                return self._estimate_nash_point(bids, my_bid_last_util)
            else:
                # opponent did not concede. Don't retaliate. Expand search space
                return my_bid_last
                

    def _estimate_nash_point(self, bids, my_bid_util):
        best_bid_for_op = None
        max_nash = 0
        for bid in bids:
            op_bid_util = self.opponent_model.getUtility(bid)
            nash = op_bid_util * my_bid_util
            if nash > max_nash:
                best_bid_for_op = bid
                max_nash = nash

        return best_bid_for_op

from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.bidspace.Interval import Interval
from geniusweb.PriorityQueue import PriorityQueue

from decimal import Decimal
from random import randint


class TitForTat:
    def __init__(self, profile, opponent_model, alpha, domain):
        self._profile = profile
        self.opponent_model = opponent_model
        self._floor = alpha
        self._ceiling = 0.9
        self._domain = domain
        self._domain_size = len(self._domain.getIssues())
        self._bid_provider = BidsWithUtility.create(self._profile)

    def find_bid(self, op_bid, my_last_bid):
        # If we are first to bid or respond generate a bid between floor and 0.85
        if op_bid is None or my_last_bid is None:
            range = Interval(Decimal(self._floor), Decimal(0.8))
            bids = self._bid_provider.getBids(range)
        # else, reciprocate by copying opponents move.
        else:
            # Measure the difference between utilities of my and op LAST bids.
            # based on my utility function
            op_bid_util = self._profile.getUtility(op_bid)
            my_bid_util = self._profile.getUtility(my_last_bid)
            util_diff = abs(op_bid_util - my_bid_util) * Decimal(0.5)
            range = None

            if op_bid_util > my_bid_util:
                # opponent made a good deal for my utility and we
                # are reciprocating by making the deal for us worse
                range = Interval(
                    Decimal(my_bid_util - util_diff),
                    Decimal(op_bid_util),
                )
            else:
                # opponent made a bad deal for us we are
                # increasing our next bids utility
                range = Interval(
                    Decimal(self._floor), Decimal(min(my_bid_util + util_diff, 1.0))
                )

            print(range)

        # Find a bid that is best for the opponent using opponent model
        bids = self._bid_provider.getBids(range)
        best_bid_for_op = bids.get(0)
        for bid in bids:
            if self.opponent_model.getUtility(bid) > self.opponent_model.getUtility(
                best_bid_for_op
            ):
                best_bid_for_op = bid

        return best_bid_for_op

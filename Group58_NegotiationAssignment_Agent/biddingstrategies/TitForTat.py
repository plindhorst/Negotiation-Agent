from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.bidspace.Interval import Interval
from geniusweb.issuevalue.Bid import Bid
from tudelft.utilities.immutablelist.ImmutableList import ImmutableList

from decimal import Decimal
from random import randint
from queue import Queue


class TitForTat:
    def __init__(self, profile, opponent_model, alpha, domain):
        self._profile = profile
        self.opponent_model = opponent_model
        self._floor = alpha
        self._ceiling = alpha + 0.1
        self._domain = domain
        self._domain_size = len(self._domain.getIssues())
        self._bid_provider = BidsWithUtility.create(self._profile)

    def find_bid(self, op_bids: Queue, my_bid_last: Bid):
        # If we are first to bid or respond generate the maximum bid
        if op_bids.qsize() < 2 or my_bid_last is None:
            return self._bid_provider.getExtremeBid(isMax=True)
        # else, reciprocate by copying opponents move.
        else:
            # Measure the difference between utilities of the last two opponent bids.
            # based on my utility function
            op_bid_old = op_bids.get()
            op_bid_new = op_bids.get()
            # put back the newest bid as oldest now
            op_bids.put(op_bid_new)

            my_bid_last_util = self._profile.getUtility(my_bid_last)
            op_bid_old_util = self._profile.getUtility(op_bid_old)
            op_bid_new_util = self._profile.getUtility(op_bid_new)
            util_diff = abs(op_bid_old_util - op_bid_new_util) * Decimal(0.6)
            interval_range = None
            if op_bid_new_util > op_bid_old_util:
                # first check if the opponent's bid is outside our reservation range
                # if this is true, search for optimal bid within our range, else
                # if the new offer has higher util than before
                # opponent made a concession for my utility and we
                # are reciprocating by also making a concession
                if op_bid_new_util > self._ceiling:
                    interval_range = Interval(
                        Decimal(self._floor),
                        Decimal(self._ceiling),
                    )
                elif op_bid_new_util < self._floor:
                    interval_range = Interval(
                        Decimal(self._floor),
                        Decimal(my_bid_last_util),
                    )
                else:
                    interval_range = Interval(
                        Decimal(my_bid_last_util - util_diff),
                        Decimal(my_bid_last_util),
                    )

                bids = self._bid_provider.getBids(interval_range)
                # Prevent having empty bids by returning our previous bid
                final_bid = my_bid_last
                # If there are bids within the range
                if bids.size() > 0:
                    # Find a bid that is best for the opponent using opponent model
                    final_bid = self._estimate_nash_point(bids, my_bid_last_util)

                return final_bid
            else:
                # opponent did not concede. Don't retaliate. Expand search space. Still check for reservation range.
                final_bid = my_bid_last
                if my_bid_last_util > self._ceiling:
                    interval_range = Interval(
                        Decimal(self._floor),
                        Decimal(self._ceiling),
                    )
                    # Again same as before, if bids empty, return previous bid
                    # Else look for optimal bid
                    bids = self._bid_provider.getBids(interval_range)
                    final_bid = my_bid_last
                    if bids.size() > 0:
                        final_bid = self._estimate_nash_point(bids, my_bid_last_util)

                return final_bid

    def _estimate_nash_point(self, bids, my_bid_util) -> Bid:
        best_bid_for_op = None
        max_nash = -1
        for bid in bids:
            op_bid_util = self.opponent_model.getUtility(bid)
            nash = op_bid_util * my_bid_util
            if nash > max_nash:
                best_bid_for_op = bid
                max_nash = nash

        return best_bid_for_op

    def update_alpha(self, alpha):
        self._floor = alpha
        self._ceiling = alpha + 0.1

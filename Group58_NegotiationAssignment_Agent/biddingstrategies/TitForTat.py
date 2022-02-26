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
        self._ceiling = 0.9
        self._domain = domain
        self._domain_size = len(self._domain.getIssues())
        self._bid_provider = BidsWithUtility.create(self._profile)

    def find_bid(self, op_bids: Queue, my_bid_last: Bid):
        # If we are first to bid or respond generate a bid between floor and 0.85
        if op_bids.qsize() < 2 or my_bid_last is None:
            range = Interval(Decimal(0.85), Decimal(0.95))
            bids = self._bid_provider.getBids(range)
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
            util_diff = abs(op_bid_old_util - op_bid_new_util)
            print(util_diff)
            range = None
            if op_bid_new_util > op_bid_old_util:
                # if the new offer has higher util than before
                # opponent made a concession for my utility and we
                # are reciprocating by also making a concession
                range = Interval(
                    Decimal(self._floor),
                    Decimal(my_bid_last_util - util_diff),
                )

                print("conceded")
            else:
                # opponent did not concede. Don't retaliate. Expand search space
                range = Interval(
                    Decimal(my_bid_last_util - Decimal(0.05)),
                    Decimal(my_bid_last_util + Decimal(0.05)),
                )
                print("not")

            print(range)
            bids = self._bid_provider.getBids(range)
            # Prevent having empty bids list by expanding it slightly till we find bids
            while bids.size() == 0:
                range.add(Interval(Decimal(-0.01), Decimal(0.01)))
                bids = self._bid_provider.getBids(range)

        # Find a bid that is best for the opponent using opponent model
        best_bid_for_op = self._find_best_bid(
            bids
        )  # bids.get(randint(0, bids.size() - 1))
        return best_bid_for_op

    def _find_best_bid(self, bids) -> Bid:
        best_bid_for_op = bids.get(randint(0, bids.size() - 1))
        for bid in bids:
            if self.opponent_model.getUtility(bid) > self.opponent_model.getUtility(
                best_bid_for_op
            ):
                best_bid_for_op = bid

        return best_bid_for_op

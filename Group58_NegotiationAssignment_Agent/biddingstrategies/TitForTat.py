from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.bidspace.Interval import Interval
from geniusweb.issuevalue.Bid import Bid

from decimal import Decimal
from random import randint


class TitForTat:
    def __init__(self, profile, opponent_model, alpha, domain):
        self._profile = profile
        self.opponent_model = opponent_model
        self._floor = alpha
        self._ceiling = 0.7
        self._domain = domain
        self._domain_size = len(self._domain.getIssues())
        self._bid_provider = BidsWithUtility.create(self._profile)

        # TODO Think about how to mirror bids not in terms of utility but in terms of concession!

    def find_bid(self, op_bid_cur, op_bid_old, my_bid_last):
        # If we are first to bid or respond generate a bid between floor and 0.85
        if op_bid_cur is None or op_bid_old is None or my_bid_last is None:
            range = Interval(Decimal(self._floor), Decimal(self._ceiling))
            bids = self._bid_provider.getBids(range)
        # else, reciprocate by copying opponents move.
        else:
            # Measure the difference between utilities of the last two opponent bids.
            # based on my utility function
            my_bid_last_util = self._profile.getUtility(my_bid_last)
            op_bid_cur_util = self._profile.getUtility(op_bid_cur)
            op_bid_old_util = self._profile.getUtility(op_bid_old)
            util_diff = abs(op_bid_old_util - op_bid_cur_util)
            range = None
            if op_bid_cur_util > op_bid_old_util:
                # if the new offer has higher util than before
                # opponent made a concession for my utility and we
                # are reciprocating by making the deal for us worse
                range = Interval(
                    Decimal(max(my_bid_last_util - util_diff, self._floor)),
                    Decimal(my_bid_last_util),
                )
                print("conceded")
            else:
                # opponent did not concede. Don't retaliate.
                range = Interval(
                    Decimal(self._floor),
                    Decimal(my_bid_last_util),
                )
                print("not")
            print(range)
            bids = self._bid_provider.getBids(range)

        # Find a bid that is best for the opponent using opponent model
        best_bid_for_op = bids.get(randint(0, bids.size() - 1))
        print(self.opponent_model.getUtility(best_bid_for_op))
        return best_bid_for_op

    def _find_best_bid(self, bids) -> Bid:
        best_bid_for_op = bids.get(randint(0, bids.size() - 1))
        for bid in bids:
            if self.opponent_model.getUtility(bid) > self.opponent_model.getUtility(
                best_bid_for_op
            ):
                best_bid_for_op = bid

        return best_bid_for_op

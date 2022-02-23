from random import randint

from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.issuevalue.Bid import Bid


class TradeOff:
    def __init__(self, profile, opponent_model, alpha, domain):
        self._profile = profile
        self._opponent_model = opponent_model
        self._alpha = alpha
        self._domain = domain
        self._issues = domain.getIssues()

    def _random_bid(self):
        all_bids = AllBidsList(self._domain)
        for _ in range(200):
            bid = all_bids.get(randint(0, all_bids.size() - 1))
            if self._profile.getUtility(bid) >= self._alpha:
                return bid

    # Find a bid by using trade off strategy.
    def find_bid(self, last_opponent_bid):
        # TODO: fix
        # if last_opponent_bid is not None:
        #     # make dict for new bid.
        #     values = {}
        #
        #     # for each issue, get value from domain and value from opponent's bid
        #     for issue in self._issues:
        #         opponent_value = self._opponent_model.get_best_value(issue)
        #         values = self._domain.getValues(issue)
        #         values[issue] = _find_trade_off(issue, values, opponent_value, last_opponent_bid)
        #
        #     return Bid(values)
        # else:
        return self._random_bid()


# Find trade off between own preference and other.
def _find_trade_off(issue, values, opponent_value, last_opponent_bid):
    last_bid_value = last_opponent_bid.getValue(issue)

    # now we have values, last_value and opponentValue
    # for example values are [0, 1, 2, 3, 4, 5],
    # our last value was 0 (highest utility for us)
    # their last value was 5 (highest utility for them)
    # we want to concede towards that (so bid for 1,2,3 or 4)
    # however when we concede on the issue of most interest to other
    # we want to gain on a issue with most interest to us.

    # stupid code:
    position_1 = -1
    position_2 = -1
    for i in range(values.size()):
        if values.get(i) == last_bid_value:
            position_1 = i
        if values.get(i) == opponent_value:
            position_2 = i

    # Case we can concede a step
    if position_1 > position_2:
        return values.get(position_1 - 1)
    if position_1 < position_2:
        return values.get(position_1 + 1)
    else:
        return last_bid_value

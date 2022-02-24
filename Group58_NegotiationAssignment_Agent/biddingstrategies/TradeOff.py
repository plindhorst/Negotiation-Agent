from random import randint
from typing import cast

from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.profile.utilityspace.LinearAdditive import LinearAdditive
from geniusweb.bidspace.Interval import Interval
from decimal import Decimal

from Group58_NegotiationAssignment_Agent.biddingstrategies.TradeOffSimilarity import TradeOffSimilarity


class TradeOff:
    def __init__(self, profile, opponent_model, offer, domain):
        self._profile = profile
        self._opponent_model = opponent_model
        self._offer = offer
        self._tolerance = 0.1
        self._domain = domain
        self._issues = domain.getIssues()
        self._utilspace = self._setUtilSpace()
        self._bidUtils = BidsWithUtility.create(self._utilspace) 
        self._tradeOffSimilarity = TradeOffSimilarity.create(self._opponent_model, self._domain)

    # Set the util space.
    def _setUtilSpace(self) -> LinearAdditive:
        return cast(LinearAdditive, self._profile)

    # Return set of iso curve bids.
    def _iso_bids(self):
        return self._bidUtils.getBids(
            Interval(Decimal.from_float(self._offer - self._tolerance), Decimal.from_float(self._offer))
        )

    # Find a bid by using trade off strategy.
    def find_bid(self, last_opponent_bid):
        # generate n bids
        bids = self._iso_bids()
        if last_opponent_bid is None:
            return bids.get(0)

        best_bid = bids.get(0)
        max_sim = 0
        for bid in bids:
            sim = self._tradeOffSimilarity._similarity(bid)
            max_sim = sim if sim > max_sim else max_sim
            best_bid = bid if sim > max_sim else best_bid

        return best_bid
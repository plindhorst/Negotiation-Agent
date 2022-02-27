from typing import cast

from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.profile.utilityspace.LinearAdditive import LinearAdditive
from geniusweb.bidspace.Interval import Interval
from decimal import Decimal
from Group58_NegotiationAssignment_Agent.Constants import Constants
from Group58_NegotiationAssignment_Agent.biddingstrategies.TitForTat import TitForTat


class TradeOff:
    def __init__(self, profile, opponent_model, offer, domain):
        self._profile = profile
        self._opponent_model = opponent_model
        self._offer = offer
        self._tolerance = Constants.iso_bids_tolerance
        self._domain = domain
        self._issues = domain.getIssues()
        self._bidUtils = BidsWithUtility.create(self._profile) 
        self._tft = TitForTat(self._profile, self._opponent_model, self._offer)

    # Return set of iso curve bids.
    def _iso_bids(self):
        return self._bidUtils.getBids(
            Interval(Decimal.from_float(self._offer - self._tolerance), Decimal.from_float(self._offer + self._tolerance))
        )
            
    # Find a bid by using trade off strategy.
    def find_bid(self, offer, last_opponent_bid):
        self._offer = offer
        # generate n bids
        bids = self._iso_bids()
        if last_opponent_bid is None:
            return bids.get(0)

        best_bid = bids.get(0)
        max_sim = 0
        for bid in bids:
            sim = self._similarity(bid)
            if (sim > max_sim):
                best_bid = bid
                max_sim = sim

        return best_bid


    def _similarity(self, bid):
        total_sim = 0
        for issue in self._domain.getIssues():
            value = bid.getValue(issue)
            total_sim += self._opponent_model._getFraction(issue, value)
        
        x = total_sim

        return x
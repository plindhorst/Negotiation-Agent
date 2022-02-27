from typing import cast

from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.profile.utilityspace.LinearAdditive import LinearAdditive
from geniusweb.bidspace.Interval import Interval
from decimal import Decimal
from Group58_NegotiationAssignment_Agent.Constants import Constants
from Group58_NegotiationAssignment_Agent.biddingstrategies.TitForTat import TitForTat

from Group58_NegotiationAssignment_Agent.biddingstrategies.TradeOffSimilarity import TradeOffSimilarity


class TradeOff:
    def __init__(self, profile, opponent_model, offer, domain):
        self._profile = profile
        self._opponent_model = opponent_model
        self._offer = offer
        self._boulware = offer
        self._tolerance = Constants.iso_bids_tolerance
        self._domain = domain
        self._issues = domain.getIssues()
        self._utilspace = self._setUtilSpace()
        self._bidUtils = BidsWithUtility.create(self._utilspace) 
        self._tradeOffSimilarity = TradeOffSimilarity.create(self._opponent_model, self._domain)
        self._tft = TitForTat(self._profile, self._opponent_model, self._offer)

    # Set the util space.
    def _setUtilSpace(self) -> LinearAdditive:
        return cast(LinearAdditive, self._profile)

    # Return set of iso curve bids.
    def _iso_bids(self):
        return self._bidUtils.getBids(
            Interval(Decimal.from_float(self._offer - self._tolerance), Decimal.from_float(self._offer + self._tolerance))
        )

    # Return value which starts at offer and goes down in a boulware fashion
    def _time_dependent(self, progress):
        if (progress > Constants.boulware_time_limit and self._boulware > Constants.floor):
            self._boulware = self._boulware - (Constants.boulware_conceding_speed * progress)
            
        return self._boulware 

    # Find a bid by using trade off strategy.
    def find_bid(self, last_opponent_bid, opponent_bids, progress):

        #offer = Max(floor, (TFT * (1 - time) + Time_Dependent * time))
        #self._offer = max(0.6, float(self._tft.find_offer(opponent_bids)) * (1.0 - progress) + self._time_dependent(progress) * progress)
        

        # generate n bids
        bids = self._iso_bids()
        if last_opponent_bid is None:
            return bids.get(0)


        self._offer = max(self._time_dependent(progress), float(self._tft.find_offer(opponent_bids)))
        print(self._offer, progress)

        best_bid = bids.get(0)
        max_sim = 0
        for bid in bids:
            sim = self._tradeOffSimilarity._similarity(bid)
            if (sim > max_sim):
                best_bid = bid
                max_sim = sim

        return best_bid
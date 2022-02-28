from random import randint
from typing import cast

from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.bidspace.BidsWithUtility import BidsWithUtility
from geniusweb.profile.utilityspace.LinearAdditive import LinearAdditive
from geniusweb.bidspace.Interval import Interval
from decimal import Decimal

from Group58_NegotiationAssignment_Agent.Constants import Constants


class TradeOff:
    def __init__(self, profile, opponent_model, offer, domain):
        self._profile = profile
        self._opponent_model = opponent_model
        self._offer = offer
        self._tolerance = Constants.iso_bids_tolerance
        self._domain = domain
        self._issues = domain.getIssues()
        self._utilspace = self._setUtilSpace()
        self._bidUtils = BidsWithUtility.create(self._utilspace)

    # Set the util space.
    def _setUtilSpace(self) -> LinearAdditive:
        return cast(LinearAdditive, self._profile)

    # Return set of iso curve bids.
    def _iso_bids(self, n=50):
        all_bids = AllBidsList(self._domain)
        bids = []
        for i, bid in enumerate(all_bids):
            if self._offer + self._tolerance > self._profile.getUtility(bid) > self._offer - self._tolerance:
                bids.append(bid)
                i += 1
            if i == n:
                break
        return bids

    # Return a random bid.
    def _getRandomBid(self):
        allBids = AllBidsList(self._domain)
        return allBids.get(randint(0, allBids.size() - 1))

    # Calculate similarity based on opponent model.
    def _similarity(self, bid):
        total_sim = 0
        for issue in self._domain.getIssues():
            value = bid.getValue(issue)
            total_sim += self._opponent_model._getFraction(issue, value)

        x = total_sim

        return x

    # Decrease our utility if we do not make any progress
    def _decrease_offer(self, received_bids, sent_bids, boulware):
        if (len(sent_bids) > 2):
            utilLast = self._profile.getUtility(sent_bids[len(sent_bids) - 1])
            utilThreeStepsAgo = self._profile.getUtility(sent_bids[len(sent_bids) - 3])

            opponentUtilLast = self._profile.getUtility(received_bids[len(received_bids) - 1])
            opponentUtilOneStepAgo = self._profile.getUtility(received_bids[len(received_bids) - 2])
            if (utilLast == utilThreeStepsAgo and opponentUtilLast <= opponentUtilOneStepAgo):
                self._offer = boulware

    # Find a bid by using trade off strategy.
    def find_bid(self, opponent_model, last_opponent_bid, received_bids, sent_bids, boulware):
        self._opponent_model = opponent_model

        self._decrease_offer(received_bids, sent_bids, boulware)

        # generate n bids
        bids = self._iso_bids()

        if last_opponent_bid is None:
            if bids.size() > 0:
                return bids.get(0)
            else:
                return self._getRandomBid()

        best_bid = bids.get(0)
        max_util = 0
        for bid in bids:
            util = self._opponent_model.getUtility(bid)
            if (util > max_util):
                best_bid = bid
                max_util = util

        return best_bid

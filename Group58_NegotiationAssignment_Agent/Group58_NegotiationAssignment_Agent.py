from copy import copy
import logging
import profile
from random import randint
from typing import Dict, cast

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Action import Action
from geniusweb.actions.Offer import Offer
from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Finished import Finished
from geniusweb.inform.Inform import Inform
from geniusweb.inform.Settings import Settings
from geniusweb.inform.YourTurn import YourTurn
from geniusweb.issuevalue.Bid import Bid
from geniusweb.issuevalue.Value import Value
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)

from Group58_NegotiationAssignment_Agent.OpponentModel import OpponentModel


class Group58_NegotiationAssignment_Agent(DefaultParty):
    """
    Template agent that offers random bids until a bid with sufficient utility is offered.
    """

    def __init__(self):
        super().__init__()
        self.getReporter().log(logging.INFO, "party is initialized")
        self._profile = None
        self._last_received_bid: Bid = None
        self._last_sent_bid: Bid = None
        self.opponent_model = None
        self.alpha = 0.6

    def notifyChange(self, info: Inform):
        """This is the entry point of all interaction with your agent after is has been initialised.

        Args:
            info (Inform): Contains either a request for action or information.
        """

        # a Settings message is the first message that will be send to your
        # agent containing all the information about the negotiation session.
        if isinstance(info, Settings):
            self._settings: Settings = cast(Settings, info)
            self._me = self._settings.getID()

            # progress towards the deadline has to be tracked manually through the use of the Progress object
            self._progress = self._settings.getProgress()

            # the profile contains the preferences of the agent over the domain
            self._profile = ProfileConnectionFactory.create(
                info.getProfile().getURI(), self.getReporter()
            )

            self.opponent_model = OpponentModel(self._profile.getProfile().getDomain())

        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            # if it is an offer, set the last received bid
            if isinstance(action, Offer):
                self._last_received_bid = cast(Offer, action).getBid()
        # YourTurn notifies you that it is your turn to act
        elif isinstance(info, YourTurn):
            # execute a turn
            self._myTurn()

            # log that we advanced a turn
            self._progress = self._progress.advance()

        # Finished will be send if the negotiation has ended (through agreement or deadline)
        elif isinstance(info, Finished):
            # terminate the agent MUST BE CALLED
            self.terminate()
        else:
            self.getReporter().log(
                logging.WARNING, "Ignoring unknown info " + str(info)
            )

    # lets the geniusweb system know what settings this agent can handle
    # leave it as it is for this course
    def getCapabilities(self) -> Capabilities:
        return Capabilities(
            set(["SAOP"]),
            set(["geniusweb.profile.utilityspace.LinearAdditive"]),
        )

    # terminates the agent and its connections
    # leave it as it is for this course
    def terminate(self):
        self.getReporter().log(logging.INFO, "party is terminating:")
        super().terminate()
        if self._profile is not None:
            self._profile.close()
            self._profile = None

    #######################################################################################
    ########## THE METHODS BELOW THIS COMMENT ARE OF MAIN INTEREST TO THE COURSE ##########
    #######################################################################################

    # give a description of your agent
    def getDescription(self) -> str:
        return "Template agent for Collaborative AI course"

    # execute a turn
    def _myTurn(self):
        # generate a bid for the opponent
        bid = None
        if self._last_sent_bid is None:
            bid = self._findBid()
        else:
            bid = self._findBid_trade_off()

        if self._last_received_bid is not None:
            self.opponent_model.update_frequencies(self._last_received_bid)
        # check if the last received offer from the opponent is good enough
        if self._isGood(self._last_received_bid, bid):
            # if so, accept the offer
            action = Accept(self._me, self._last_received_bid)
        else:
            # if not, counter offer
            self._last_sent_bid = copy(bid)
            opponent_utility = self.opponent_model.utility(bid)
            action = Offer(self._me, bid)

        # send the action
        self.getConnection().send(action)

    # method that checks if we would agree with an offer
    def _isGood(self, opponent_bid: Bid, my_bid: Bid) -> bool:
        if opponent_bid is None:
            return False
        profile = self._profile.getProfile()

        progress = self._progress.get(0)

        # very basic approach that accepts if the offer is valued above 0.6 and
        # 80% of the rounds towards the deadline have passed

        return (
            self._ac_next(opponent_bid, my_bid)
            or profile.getUtility(my_bid) > self.alpha
            and progress > 0.8
        )

    def _findBid(self) -> Bid:
        # compose a list of all possible bids
        domain = self._profile.getProfile().getDomain()
        all_bids = AllBidsList(domain)

        # Check if we are offering first
        offering_first = False
        if self._last_received_bid is None:
            offering_first = True

        # take 50 attempts at finding a random bid that is acceptable to us
        for _ in range(200):
            bid = all_bids.get(randint(0, all_bids.size() - 1))
            # If we are the first ones to offer, check only that the utility is high
            if (
                offering_first
                and self._profile.getProfile().getUtility(bid) > self.alpha
            ):
                break
            elif self._isGood(self._last_received_bid, bid):
                break
        return bid

    # Find a bid by using trade off strategy.
    def _findBid_trade_off(self) -> Bid:
        opponentModel = self.opponent_model

        domain = self._profile.getProfile().getDomain()
        issues = domain.getIssues()

        # make dict for new bid.
        issueValues: Dict[str, Value] = {}

        # for each issue, get value from domain and value from opponent's bid
        for iss in issues:
            opponentValue = opponentModel.get_best_value(iss)
            values = domain.getValues(iss)

            issueValues[iss] = self._find_trade_off(iss, values, opponentValue)

        return Bid(issueValues)

    # Find trade off between own preference and other.
    def _find_trade_off(self, issue, values, opponentValue) -> Value:
        if self._last_sent_bid is not None:
            lbid = self._last_sent_bid
            # check if we can concede
            lval = lbid.getValue(issue)

            profile = self._profile.getProfile()

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
                if values.get(i) == lval:
                    position_1 = i
                if values.get(i) == opponentValue:
                    position_2 = i

            # Case we can concede a step
            if position_1 > position_2:
                return values.get(position_1 - 1)
            if position_1 < position_2:
                return values.get(position_1 + 1)
            else:
                return lval

        else:
            return values.get(0)

    def _ac_next(self, opponont_bid: Bid, my_bid: Bid) -> bool:
        prof = self._profile.getProfile()
        return prof.getUtility(opponont_bid) > prof.getUtility(my_bid)

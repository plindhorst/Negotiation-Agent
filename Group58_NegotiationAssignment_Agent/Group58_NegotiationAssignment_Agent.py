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
from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel

#from Group58_NegotiationAssignment_Agent.opponentmodels.OpponentModel import OpponentModel

from Group58_NegotiationAssignment_Agent.acceptancestrategies.AcceptanceStrategy import AcceptanceStrategy
from Group58_NegotiationAssignment_Agent.biddingstrategies.TradeOffSimilarity import TradeOffSimilarity


class Group58_NegotiationAssignment_Agent(DefaultParty):
    """
    Template agent that offers random bids until a bid with sufficient utility is offered.
    """

    def __init__(self):
        super().__init__()

        self.getReporter().log(logging.INFO, "party is initialized")
        self._profile = None
        self._last_received_bid = None
        self._last_sent_bid = None
        self.opponent_model = None
        self.alpha = 0.75
        self.ceiling = 0.95
        self.bidding_strat = None
        self.acceptance_strat = None

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

            # BOA initializing
            self.opponent_model = FrequencyOpponentModel.create()
            self.bidding_strat = TradeOffSimilarity(self._profile.getProfile(), self.opponent_model, self.alpha,
                                                    self.ceiling, self._profile.getProfile().getDomain())
            self.acceptance_strat = AcceptanceStrategy(self._profile.getProfile(), self.alpha,
                                                       self._profile.getProfile().getDomain())

        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            # update opponent model
            if self._last_received_bid is not None:
                self.opponent_model = self.opponent_model.WithAction(action, self._progress)

            # if it is an offer, set the last received bid
            if isinstance(action, Offer):
                self._last_received_bid = cast(Offer, action).getBid()
                self.opponent_model = self.opponent_model.With(self._profile.getProfile().getDomain(), self._last_received_bid)
        # YourTurn notifies you that it is your turn to act
        elif isinstance(info, YourTurn):
            # execute a turn
            self._my_turn()

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
    def _my_turn(self):

        # generate a bid for the opponent
        self.update_alpha()
        bid = self.bidding_strat.find_bid(self._last_received_bid)
        if self._profile.getProfile().getUtility(bid) > self.ceiling:
            bid = self.bidding_strat.find_bid(self._last_received_bid)

        # check if opponents bid is better than ours, if yes then accept, else offer our bid
        if self.is_good(self._last_received_bid, bid, self._progress.get(0)):
            self.getConnection().send(Accept(self._me, self._last_received_bid))
        else:
            self.getConnection().send(Offer(self._me, bid))

    def is_good(self, opponent_bid, my_bid, progress):
        # very basic approach that accepts if the offer is valued above alpha and
        # 80% of the rounds towards the deadline have passed

        return (
                self._accept_next(opponent_bid, my_bid)
                or self._profile.getProfile().getUtility(my_bid) > self.alpha
                and progress > 0.9
        )

    def _accept_next(self, opponent_bid, my_bid):
        return opponent_bid is not None and self._profile.getProfile().getUtility(opponent_bid) > \
               self._profile.getProfile().getUtility(my_bid)

    def update_alpha(self):
        if self._progress.get(0) > 0.5:
            self.alpha = self.alpha - (0.01 * self._progress.get(0))
            self.ceiling = self.alpha + 0.2

import logging

from typing import cast

import decimal
from copy import copy
import logging
import profile
from random import randint
from typing import Dict, cast
from queue import Queue

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Action import Action
from geniusweb.actions.Offer import Offer
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Finished import Finished
from geniusweb.inform.Inform import Inform
from geniusweb.inform.Settings import Settings
from geniusweb.inform.YourTurn import YourTurn
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty

from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel

from geniusweb.progress.ProgressRounds import ProgressRounds

from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)

from Group58_NegotiationAssignment_Agent.Constants import Constants
from Group58_NegotiationAssignment_Agent.acceptancestrategies.AcceptanceStrategy import AcceptanceStrategy
from Group58_NegotiationAssignment_Agent.biddingstrategies.TradeOff import TradeOff

from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel
from Group58_NegotiationAssignment_Agent.acceptancestrategies.AcceptanceStrategy import (
    AcceptanceStrategy,
)
from Group58_NegotiationAssignment_Agent.biddingstrategies.TitForTat import (
    TitForTat,
)


class Group58_NegotiationAssignment_Agent(DefaultParty):
    """
    Template agent that offers random bids until a bid with sufficient utility is offered.
    """

    def __init__(self):
        super().__init__()

        self.getReporter().log(logging.INFO, "party is initialized")
        self._profile = None
        self._last_received_bid = None
        self._received_bids = []
        self._sent_bids = []
        self.opponent_model = None
        self.offer = Constants.offer
        self.floor = Constants.floor
        self.boulware = self.offer
        self._opponent_bids = Queue()
        self._last_proposed_bid = None
        self.opponent_model = None
        self.alpha = 0.85
        self.bidding_strat = None
        self.acceptance_strat = None
        self.previous_progress = 0

    def notifyChange(self, info: Inform):
        """This is the entry point of all interaction with your agent after is has been initialised.

        Args:
            info (Inform): Contains either a request for action or information.
        """

        # a Settings message is the first message that will be send to your
        # agent containing all the information about the negotiation session.
        # Only executed once!
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

            self.opponent_model = FrequencyOpponentModel.create().With(self._profile.getProfile().getDomain(), None)
            open('OpponentModel.log', 'w').close()
            self.bidding_strat = TradeOff(self._profile.getProfile(), self.opponent_model, self.offer,
                                          self._profile.getProfile().getDomain())
            self.acceptance_strat = AcceptanceStrategy(self._profile.getProfile(), self.floor,
                                                       self._profile.getProfile().getDomain())

            # self.opponent_model = FrequencyOpponentModel.create()
            # self.opponent_model = self.opponent_model.With(
            #     self._profile.getProfile().getDomain(), None
            # )
            # self.bidding_strat = TitForTat(
            #     self._profile.getProfile(),
            #     self.opponent_model,
            #     self.alpha,
            #     self._profile.getProfile().getDomain(),
            # )
            # self.acceptance_strat = AcceptanceStrategy(
            #     self._profile.getProfile(),
            #     self.alpha,
            #     self._profile.getProfile().getDomain(),
            # )


        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            # if it is an offer, set the last received bid
            if isinstance(action, Offer) and action.getActor().getName() != self._me.getName():
                self._last_received_bid = cast(Offer, action).getBid()
                self._received_bids.append(self._last_received_bid)
                self.opponent_model = self.opponent_model.WithAction(action, self._progress)

            # # if it is an offer, set the last received bid,
            # # also check if the bid did not come from us so to not
            # # confuse the opponent model
            # if isinstance(action, Offer) and "58" not in action.getActor().getName():
            #     self._last_received_bid = cast(Offer, action).getBid()
            #     if self._opponent_bids.qsize() < 2:
            #         self._opponent_bids.put(
            #             Bid(self._last_received_bid.getIssueValues())
            #         )
            #
            #     self.opponent_model = self.opponent_model.WithAction(
            #         action, self._progress
            #     )
            #     self.bidding_strat.opponent_model = self.opponent_model


        # YourTurn notifies you that it is your turn to act
        elif isinstance(info, YourTurn):
            # execute a turn
            self._my_turn()

            # log that we advanced a turn
            if isinstance(self._progress, ProgressRounds):
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
        return "Trade-Off/TitForTat hyrbrid negotiation agent"

    def TimeDependent(self):
        if self._progress.get(0) > Constants.boulware_time_limit and self.offer > Constants.floor:
            self.boulware = self.boulware - (Constants.boulware_conceding_speed * self._progress.get(0))

    # execute a turn
    def _my_turn(self):

        self.TimeDependent()
        # generate a bid for the opponent
        bid = self.bidding_strat.find_bid(self.opponent_model, self._last_received_bid, self._received_bids,
                                          self._sent_bids, self.boulware)

        self._update_alpha()
        bid = self.bidding_strat.find_bid(
            self._opponent_bids,
            self._last_proposed_bid,
        )

        # check if opponents bid is better than ours, if yes then accept, else offer our bid
        if self._last_received_bid is not None and self.acceptance_strat.is_good(
                self._last_received_bid, bid, self._progress.get(0)
        ):
            self.getConnection().send(Accept(self._me, self._last_received_bid))
        else:

            # save expected utility for OM graph
            with open("OpponentModel.log", "a") as text_file:
                text_file.write(str(self.opponent_model.getUtility(bid)) + "\n")

            self.getConnection().send(Offer(self._me, bid))
            self._sent_bids.append(bid)

    #         self._last_proposed_bid = bid
    #         action = Offer(self._me, bid)
    #     self.previous_progress = self._progress.get(0)
    #     self.getConnection().send(action)
    #
    # Update the floor and ceiling values over time
    # Starting at 0.85 and ending at 0.65
    # This makes 0.65 our reservation value
    # Decreases linearly, amount of rounds shouldn't affect the linear rate
    def _update_alpha(self):
        self.alpha = self.alpha - 0.2 * (self._progress.get(0) - self.previous_progress)
        self.bidding_strat.update_alpha(self.alpha)

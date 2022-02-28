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
from geniusweb.progress.ProgressRounds import ProgressRounds
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)

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

            print("BID", self._profile.getProfile().getReservationBid())

            # BOA initializing
            self.opponent_model = FrequencyOpponentModel.create()
            self.opponent_model = self.opponent_model.With(
                self._profile.getProfile().getDomain(), None
            )
            # self.opponent_model = OpponentModel(self._profile.getProfile().getDomain())
            self.bidding_strat = TitForTat(
                self._profile.getProfile(),
                self.opponent_model,
                self.alpha,
                self._profile.getProfile().getDomain(),
            )
            self.acceptance_strat = AcceptanceStrategy(
                self._profile.getProfile(),
                self.alpha,
                self._profile.getProfile().getDomain(),
            )

        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            # if it is an offer, set the last received bid
            if isinstance(action, Offer) and "58" not in action.getActor().getName():
                self._last_received_bid = cast(Offer, action).getBid()
                if self._opponent_bids.qsize() < 2:
                    self._opponent_bids.put(
                        Bid(self._last_received_bid.getIssueValues())
                    )

                # update opponent model
                # self.opponent_model.With(
                #     self._profile.getProfile().getDomain(),
                #     self.opponent_model.getReservationBid(),
                # )
                self.opponent_model = self.opponent_model.WithAction(
                    action, self._progress
                )
                self.bidding_strat.opponent_model = self.opponent_model
                # self.opponent_model.update_frequencies(self._last_received_bid)

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
        return "Template agent for Collaborative AI course"

    # execute a turn
    def _my_turn(self):

        self._update_alpha()
        bid = self.bidding_strat.find_bid(
            self._opponent_bids,
            self._last_proposed_bid,
        )

        # check if opponents bid is better than ours, if yes then accept, else offer our bid
        if self._last_received_bid is not None and self.acceptance_strat.is_good(
            self._last_received_bid, bid, self._progress.get(0)
        ):
            action = Accept(self._me, self._last_received_bid)
        else:
            self._last_proposed_bid = bid
            action = Offer(self._me, bid)
        self.previous_progress = self._progress.get(0)
        self.getConnection().send(action)

    # Update the floor and ceiling values over time
    # Starting at 0.85 and ending at 0.65
    # This makes 0.65 our reservation value
    # Decreases linearly, amount of rounds shouldn't affect the linear rate
    def _update_alpha(self):
        self.alpha = self.alpha - 0.2 * (self._progress.get(0) - self.previous_progress)
        self.bidding_strat.update_alpha(self.alpha)

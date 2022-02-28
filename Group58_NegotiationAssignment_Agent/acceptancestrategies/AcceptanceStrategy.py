class AcceptanceStrategy:
    def __init__(self, profile, alpha, domain):
        self._profile = profile
        self._alpha = alpha
        self._issues = domain.getIssues()

    # method that checks if we would agree with an offer
    def is_good(self, opponent_bid, my_bid, progress):

        return (
            self._accept_next(opponent_bid, my_bid)
            # Accept any bid higher than our floor if 90% of rounds have passed
            or self._profile.getUtility(opponent_bid) > self._alpha
            and progress > 0.9
        )

    def _accept_next(self, opponent_bid, my_bid):
        return opponent_bid is not None and self._profile.getUtility(
            opponent_bid
        ) > self._profile.getUtility(my_bid)

class AcceptanceStrategy:
    def __init__(self, profile, alpha, domain):
        self._profile = profile
        self._alpha = alpha
        self._issues = domain.getIssues()

    # method that checks if we would agree with an offer
    def is_good(self, opponent_bid, my_bid, progress):
        # very basic approach that accepts if the offer is valued above 0.6 and
        # 80% of the rounds towards the deadline have passed

        return (
            self._accept_next(opponent_bid, my_bid)
            or self._profile.getUtility(opponent_bid) > self._alpha
            and progress > 0.8
        )

    def _accept_next(self, opponent_bid, my_bid):
        return opponent_bid is not None and self._profile.getUtility(
            opponent_bid
        ) > self._profile.getUtility(my_bid)

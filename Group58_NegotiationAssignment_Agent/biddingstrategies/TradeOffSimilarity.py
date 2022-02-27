from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel

class TradeOffSimilarity:
    def __init__(self, opponent_model : FrequencyOpponentModel, domain):
        self._opponent_model = opponent_model
        self._domain = domain
        self._domain_size = len(self._domain.getIssues())


    @staticmethod
    def create(opponent_model, domain) -> "TradeOffSimilarity":
        return TradeOffSimilarity(opponent_model, domain)

    #########################################################################################
    # This function returns the similarity between a bid and the opponent's preferences.    #
    # For example the opponent has the following values in issue X from previous bids:      #
    # ValueA : 10 times                                                                     #
    # ValueB : 5 times                                                                      #
    # ValueC : 1 time                                                                       #
    #                                                                                       #
    # If the current bid has valueB for issue X then the similarity for issue X is:         #
    # 5 / 16 = 31.25%                                                                       #
    #########################################################################################
    def _similarity(self, bid):
        total_sim = 0
        for issue in self._domain.getIssues():
            value = bid.getValue(issue)
            total_sim += self._opponent_model._getFraction(issue, value)
        
        x = total_sim

        return x

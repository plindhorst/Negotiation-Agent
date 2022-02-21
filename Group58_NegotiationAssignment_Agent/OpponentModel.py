class OpponentModel:
    def __init__(self, domain):
        self._domain = domain
        self._freqs = {}
        self.opponent_bids = []
        open('OpponentModel.log', 'w').close()
        for issue in self._domain.getIssues():
            self._freqs[issue] = {}

    # Update value frequency for new incoming bid
    def update_frequencies(self, bid):
        self.opponent_bids.append(bid)
        for issue in self._domain.getIssues():
            value = bid.getValue(issue)
            if value in self._freqs[issue]:
                self._freqs[issue][value] += 1
            else:
                self._freqs[issue][value] = 1

    # get value for issue with highest frequency
    def get_best_value(self, issue):
        max = 0
        value = 0

        for val in self._freqs[issue]:
            if (self._freqs[issue][val] > max):
                max = self._freqs[issue][val]
                value = val
        
        return value

    # returns normalized weights depending on importance of the issues
    # along with the largest value freq for each issue
    def _issue_weights(self):
        # For each issue we find the highest frequency
        max_freqs = {}
        max_f = 0
        for issue in self._domain.getIssues():
            max_freqs[issue] = 0
            for value in self._freqs[issue]:
                if max_freqs[issue] < self._freqs[issue][value]:
                    max_freqs[issue] = self._freqs[issue][value]
            if max_f < max_freqs[issue]:
                max_f = max_freqs[issue]
        weights = {}
        # normalize weights
        for issue in self._domain.getIssues():
            weights[issue] = max_freqs[issue] / max_f if max_f != 0 else 0
        return weights, max_freqs

    # returns the utility of our bid to opponent
    def utility(self, bid):
        u = 0
        weights, max_freqs = self._issue_weights()
        # utility is the sum of normalized value freq * issue weight
        for issue in self._domain.getIssues():
            value = bid.getValue(issue)
            if value in self._freqs[issue]:
                u += (self._freqs[issue][bid.getValue(issue)] / max_freqs[issue]) * weights[issue]

        u /= len(self._domain.getIssues())

        # save utilities in file for future logging
        with open("OpponentModel.log", "a") as text_file:
            text_file.write(str(u) + "\n")
        return u

from random import randint

from geniusweb.bidspace.AllBidsList import AllBidsList


class TradeOffSimilarity:
    def __init__(self, profile, opponent_model, alpha, domain, generate_n=50):
        self._profile = profile
        self._opponent_model = opponent_model
        self._alpha = alpha
        self._domain = domain
        self._generate_n = generate_n
        self._domain_size = len(self._domain.getIssues())

    #TODO keep random, however bids may not be duplicate
    def _iso_bids(self):
        all_bids = AllBidsList(self._domain)
        optimal_bids = []
        i = 0

        # generate up to generate_n viable bids
        for _ in range(1000):
            bid = all_bids.get(randint(0, all_bids.size() - 1))
            if (i == self._generate_n):
                break
            if (bid in optimal_bids):
                continue
            if self._profile.getUtility(bid) >= self._alpha:
                optimal_bids.append(bid)
                i += 1
        
        return optimal_bids

    def _random_bid(self):
        all_bids = AllBidsList(self._domain)
        for _ in range(400):
            bid = all_bids.get(randint(0, all_bids.size() - 1))
            if self._profile.getUtility(bid) >= self._alpha:
                return bid

    def find_bid(self, last_opponent_bid):
        if last_opponent_bid is None:
            return self._random_bid()
        # generate n bids
        bids = self._iso_bids()
        if (len(bids) == 0):
            return self._random_bid()

        best_bid = bids[0]
        max_sim = 0
        for bid in bids:
            sim = self._similarity(bid)
            max_sim = sim if sim > max_sim else max_sim
            best_bid = bid if sim > max_sim else best_bid

        self._alpha = self._update_alpha()

        return best_bid

    def _update_alpha(self):
        #TODO update alpha according to time
        if (self._alpha > 0.6):
            return self._alpha - 0.003
        else:
            return self._alpha

    def _similarity(self, bid):
        total_sim = 0
        for issue in self._domain.getIssues():
            value = bid.getValue(issue)
            total_sim += self._opponent_model._getFraction(issue, value)
        
        x = total_sim / self._domain_size

        return x

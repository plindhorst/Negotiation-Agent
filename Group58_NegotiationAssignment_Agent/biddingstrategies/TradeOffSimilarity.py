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

    def _random_bid(self):
        all_bids = AllBidsList(self._domain)
        for _ in range(200):
            bid = all_bids.get(randint(0, all_bids.size() - 1))
            if self._profile.getUtility(bid) >= self._alpha:
                return bid

    def find_bid(self, last_opponent_bid):
        if last_opponent_bid is None:
            return self._random_bid()
        # generate n bids
        bids = []
        for i in range(self._generate_n):
            bids.append(self._random_bid())

        best_bid = bids[0]
        max_sim = 0
        for bid in bids:
            sim = self._similarity(bid, last_opponent_bid)
            max_sim = sim if sim > max_sim else max_sim
            best_bid = bid if sim > max_sim else best_bid
        return best_bid

    def _similarity(self, bid_a, bid_b):
        cosine_sim = 0
        for issue in self._domain.getIssues():
            if bid_a.getValue(issue) == bid_b.getValue(issue):
                cosine_sim += 1
        return cosine_sim / self._domain_size

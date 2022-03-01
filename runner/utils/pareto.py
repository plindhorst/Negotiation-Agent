import json

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors


def color_gradient(n):
    colors_ = []
    for j in range(n):
        c1 = np.array(mpl.colors.to_rgb("yellow"))
        c2 = np.array(mpl.colors.to_rgb("red"))
        hex_ = mpl.colors.to_hex((1 - j / n) * c1 + j / n * c2)
        colors_.append(hex_)
    return colors_


def poly(my_offer_utilities):
    m, b = np.polyfit(my_offer_utilities[:, 0], my_offer_utilities[:, 1], 1)
    plt.plot(my_offer_utilities[:, 0], m * my_offer_utilities[:, 0] + b, c='orange', label="Linear Regression",
             zorder=10)


def pareto_graph(results_trace, json_path, save_path):
    my_offer_utilities = []
    op_offer_utilities = []
    accepted_bid = None

    for action in results_trace["actions"]:
        if (
                "Offer" in action
                and "party_Group58_NegotiationAssignment_Agent" in action["Offer"]["actor"]
        ):
            my_offer_utilities.append(list(action["Offer"]["utilities"].values()))
        elif "Accept" in action:
            accepted_bid = action["Accept"]
        else:
            op_offer_utilities.append(list(action["Offer"]["utilities"].values()))

    my_offer_utilities = np.array(my_offer_utilities)
    op_offer_utilities = np.array(op_offer_utilities)

    # figure settings
    fig = plt.gcf()
    fig.clear()
    fig.set_size_inches(10, 10)
    plt.xlabel("Utility me")
    plt.ylabel("Utility opponent")
    plt.title("Negotiation trace with Pareto Frontier")

    # Plot utilities

    if len(my_offer_utilities) > 1:
        poly(my_offer_utilities)

    # earlier bids are yellow
    gradient = color_gradient(len(my_offer_utilities))
    for i, offer_utility in enumerate(my_offer_utilities):
        temp = np.zeros(len(my_offer_utilities))
        temp[i] = offer_utility[1]
        plt.scatter(offer_utility[0], offer_utility[1], c=gradient[i], s=20, zorder=10)

    if len(op_offer_utilities) > 0:
        plt.plot(op_offer_utilities[:, 0], op_offer_utilities[:, 1], c='grey', label="Opponent trace")
    # Plot accepted bid
    if accepted_bid is not None:
        x, y = accepted_bid["utilities"].values()
        plt.scatter(x, y, color="green", label="Accepted bid", s=60, zorder=11)
    # Plot Pareto Frontier
    with open(json_path) as json_file:
        pf = json.load(json_file)
        utils = []
        for bid in pf["pareto_front"]:
            utils.append(bid["utility"])

        utils = np.array(utils)
        plt.plot(utils[:, 0], utils[:, 1], color="blue", label="Pareto Front")

    plt.legend()
    plt.savefig(save_path, bbox_inches="tight")
    plt.close(fig)

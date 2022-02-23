import json
import os
import argparse

import numpy as np
from matplotlib import pyplot as plt

from runner.utils.plot_trace import plot_trace
from runner.utils.runners import run_session

DOMAIN_PATH = "runner/domains/domain02/"

# parse given flag
parser = argparse.ArgumentParser()
parser.add_argument(
    "--trace", action="store_true", help="Generates negotiation trace graph"
)

args = parser.parse_args()

# create results directory if it does not exist
if not os.path.exists("runner/results"):
    os.mkdir("runner/results")

# Settings to run a negotiation session:
#   We need to specify the classpath of 2 agents to start a negotiation.
#   We need to specify the preference profiles for both agents. The first profile will be assigned to the first agent.
#   We need to specify a deadline of amount of rounds we can negotiate before we end without agreement
settings = {
    "agents": [
        "party.Group58_NegotiationAssignment_Agent",
        "runner.agents.linear_agent.linear_agent.LinearAgent",
    ],
    "profiles": [
        DOMAIN_PATH + "profileA.json",
        DOMAIN_PATH + "profileB.json",
    ],
    "deadline_rounds": 200,
}


# run a session and obtain results in dictionaries
opponent_model, results_trace, results_summary = run_session(settings)
if "expected_utility" in opponent_model[0]:
    # plot opponent model vs. real utilities
    fig = plt.gcf()
    x = np.arange(len(opponent_model))
    real_utilities = np.vectorize(lambda x: x["utility"])(opponent_model)
    moddeled_utilities = np.round(
        np.vectorize(lambda x: x["expected_utility"])(opponent_model), 3
    )
    error = np.abs(moddeled_utilities - real_utilities)
    coef = np.polyfit(x, error, 1)
    poly1d_fn = np.poly1d(coef)
    plt.plot(x, real_utilities, c="green", label="Real")
    plt.plot(x, moddeled_utilities, c="red", label="Expected")
    plt.plot(x, poly1d_fn(x), "--k", label="Error")

    plt.xlabel("Rounds")
    plt.ylabel("Utility")
    plt.title("Opponent utility vs. expected utility model")
    plt.legend()
    fig.set_size_inches(20, 10)
    plt.savefig("runner/results/opponent model.png", bbox_inches="tight")

# If trace flag was set
if args.trace and os.path.isfile(DOMAIN_PATH + "specials.json"):
    # Gatherd utilities
    my_offer_utilities = []
    op_offer_utilities = []
    accepted_bid = None

    for action in results_trace["actions"]:
        if (
            "Offer" in action
            and action["Offer"]["actor"]
            == "party_Group58_NegotiationAssignment_Agent_1"
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
    plt.plot(my_offer_utilities[:, 0], my_offer_utilities[:, 1], "r-", label="My trace")
    plt.plot(
        op_offer_utilities[:, 0], op_offer_utilities[:, 1], "b-", label="Opponent trace"
    )
    # Plot accepted bid
    if accepted_bid is not None:
        x, y = accepted_bid["utilities"].values()
        plt.scatter(x, y, color="green", label="Accepted bid")
    # Plot Pareto Frontier
    with open(DOMAIN_PATH + "specials.json") as json_file:
        pf = json.load(json_file)
        utils = []
        for bid in pf["pareto_front"]:
            utils.append(bid["utility"])

        utils = np.array(utils)
        plt.plot(utils[:, 0], utils[:, 1], ".y-", label="Pareto Front")

    plt.legend()
    plt.savefig("runner/results/negotiation_trace.png", bbox_inches="tight")


# plot trace to html file
plot_trace(results_trace, "runner/results/trace_plot.html")

# write results to file
with open("runner/results/results_trace.json", "w") as f:
    f.write(json.dumps(results_trace, indent=2))
with open("runner/results/results_summary.json", "w") as f:
    f.write(json.dumps(results_summary, indent=2))

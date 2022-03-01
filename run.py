import argparse
import json
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from runner.utils.plot_trace import plot_trace
from runner.utils.runners import run_session

DOMAIN_PATH = "runner/domains/"

# parse given flag
parser = argparse.ArgumentParser()
parser.add_argument("--trace", action="store_true", help="Generates negotiation trace graph")
parser.add_argument("--all", action="store_true", help="Run against all agents in all domains")

args = parser.parse_args()

RESULTS_FOLDER = "runner/results"
# create results directory if it does not exist
if not os.path.exists(RESULTS_FOLDER):
    os.mkdir(RESULTS_FOLDER)

if args.all:
    agent_pairs = [
        ("party.Group58_NegotiationAssignment_Agent", "runner.agents.boulware_agent.boulware_agent.BoulwareAgent"),
        ("party.Group58_NegotiationAssignment_Agent", "runner.agents.conceder_agent.conceder_agent.ConcederAgent"),
        ("party.Group58_NegotiationAssignment_Agent", "runner.agents.hardliner_agent.hardliner_agent.HardlinerAgent"),
        ("party.Group58_NegotiationAssignment_Agent", "runner.agents.linear_agent.linear_agent.LinearAgent"),
        ("party.Group58_NegotiationAssignment_Agent", "runner.agents.random_agent.random_agent.RandomAgent"),
        ("party.Group58_NegotiationAssignment_Agent", "runner.agents.stupid_agent.stupid_agent.StupidAgent"),
        ("party.Group58_NegotiationAssignment_Agent", "runner.agents.template_agent.template_agent.TemplateAgent")]
    profile_pairs = [("domain00/profileA.json", "domain00/profileB.json"),
                     ("domain01/profileA.json", "domain01/profileB.json"),
                     ("domain02/profileA.json", "domain02/profileB.json"),
                     ("domain03/profileA.json", "domain03/profileB.json"),
                     ("domain04/profileA.json", "domain04/profileB.json"),
                     ("domain05/profileA.json", "domain05/profileB.json"),
                     ("domain06/profileA.json", "domain06/profileB.json"),
                     ("domain07/profileA.json", "domain07/profileB.json"),
                     ("domain08/profileA.json", "domain08/profileB.json"),
                     ("domain09/profileA.json", "domain09/profileB.json")]
else:
    profile_pairs = [("domain03/profileA.json", "domain03/profileB.json")]
    agent_pairs = [
        ("party.Group58_NegotiationAssignment_Agent", "runner.agents.boulware_agent.boulware_agent.BoulwareAgent")]

for profile_pair in profile_pairs:
    profile_name = profile_pair[0][:profile_pair[0].find("/")]

    results_folder = RESULTS_FOLDER + "/" + profile_name + "/"
    if not os.path.exists(results_folder):
        os.mkdir(results_folder)

    for agent_pair in agent_pairs:
        agent_name = agent_pair[1][len(agent_pair[1]) - agent_pair[1][::-1].find("."):]
        print("\nRunning against " + agent_name + " [" + profile_name + "]\n")
        # Settings to run a negotiation session:
        settings = {
            "agents": [
                agent_pair[0],
                agent_pair[1]
            ],
            "profiles": [
                DOMAIN_PATH + profile_pair[0],
                DOMAIN_PATH + profile_pair[1],
            ],
            "deadline_rounds": 200,
        }

        # run a session and obtain results in dictionaries
        results_trace, results_summary = run_session(settings)


        def color_gradient(n):
            colors = []
            for j in range(n):
                c1 = np.array(mpl.colors.to_rgb("yellow"))
                c2 = np.array(mpl.colors.to_rgb("red"))
                hex = mpl.colors.to_hex((1 - j / n) * c1 + j / n * c2)
                colors.append(hex)
            return colors


        # If trace flag was set
        if args.trace and os.path.isfile(DOMAIN_PATH + profile_name + "/specials.json"):
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

            if len(my_offer_utilities) > 0:
                m, b = np.polyfit(my_offer_utilities[:, 0], my_offer_utilities[:, 1], 1)
                plt.plot(my_offer_utilities[:, 0], m * my_offer_utilities[:, 0] + b, c='orange', label="Linear Regression",
                         zorder=10)
            # earlier bids are yellow
            gradient = color_gradient(len(my_offer_utilities))
            for i, offer_utility in enumerate(my_offer_utilities):
                temp = np.zeros(len(my_offer_utilities))
                temp[i] = offer_utility[1]
                plt.scatter(offer_utility[0], offer_utility[1], c=gradient[i], s=20, zorder=10)

            plt.plot(op_offer_utilities[:, 0], op_offer_utilities[:, 1], c='grey', label="Opponent trace")
            # Plot accepted bid
            if accepted_bid is not None:
                x, y = accepted_bid["utilities"].values()
                plt.scatter(x, y, color="green", label="Accepted bid", s=60, zorder=11)
            # Plot Pareto Frontier
            with open(DOMAIN_PATH + profile_name + "/specials.json") as json_file:
                pf = json.load(json_file)
                utils = []
                for bid in pf["pareto_front"]:
                    utils.append(bid["utility"])

                utils = np.array(utils)
                plt.plot(utils[:, 0], utils[:, 1], color="blue", label="Pareto Front")

            plt.legend()
            plt.savefig(results_folder + agent_name + ".png", bbox_inches="tight")

        # plot trace to html file
        plot_trace(results_trace, results_folder + agent_name + ".html")

        # write results to file
        with open(results_folder + agent_name + ".json", "w") as f:
            f.write(json.dumps(results_trace, indent=2))
        with open(results_folder + agent_name + ".json", "w") as f:
            f.write(json.dumps(results_summary, indent=2))

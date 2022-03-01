import argparse
import json
import os

from runner.utils.pareto import pareto_graph
from runner.utils.plot_trace import plot_trace
from runner.utils.runners import run_session

DOMAIN_PATH = "runner/domains/"
RESULTS_FOLDER = "runner/results"
ROUNDS = 200

# parse given flag
parser = argparse.ArgumentParser()
parser.add_argument("--trace", action="store_true", help="Generates negotiation trace graph")
parser.add_argument("--all", action="store_true", help="Run against all agents in all domains")

args = parser.parse_args()

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

averages = {"count": 0, "wins": 0, "num_offers": 0, "nash_product": 0, "social_welfare": 0, "agreement": 0}

# start negotiations
for profile_pair in profile_pairs:
    profile_name = profile_pair[0][:profile_pair[0].find("/")]

    # create result folder for domain
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
            "deadline_rounds": ROUNDS,
        }

        # run a session and obtain results in dictionaries
        results_trace, results_summary = run_session(settings)

        # save results
        results_summary['win'] = results_summary['result'] == "agreement" and results_summary[
            'utility_' + str(averages["count"] * 2 + 1)] > results_summary['utility_' + str(averages["count"] * 2 + 2)]
        results_summary['domain'] = profile_name
        averages["count"] += 1
        if results_summary['win']:
            averages["wins"] += 1
        averages["num_offers"] += results_summary["num_offers"]
        averages["social_welfare"] += results_summary["social_welfare"]
        if results_summary['result'] == "agreement":
            averages["agreement"] += 1

        # if trace flag was set
        if args.trace and os.path.isfile(DOMAIN_PATH + profile_name + "/specials.json"):
            pareto_graph(results_trace, DOMAIN_PATH + profile_name + "/specials.json",
                         results_folder + agent_name + ".png")

            # plot trace to html file
            plot_trace(results_trace, results_folder + agent_name + ".html")

        # write results to file
        with open(results_folder + agent_name + ".json", "w") as f:
            f.write(json.dumps(results_trace, indent=2))
        with open(results_folder + agent_name + ".json", "w") as f:
            f.write(json.dumps(results_summary, indent=2))

print(averages)

print("\n\n\n### Results: ###\n\n* Negotiations: " + str(averages["count"]) + "\n* Wins: " + str(
    round(averages["wins"] * 100 / averages["count"], 2)) + "%\n* Agreements: " + str(
    round(averages["agreement"] * 100 / averages["count"], 2)) + "%\n* Avg. Offers: " + str(
    round(averages["num_offers"] / averages["count"], 2)) + "\n* Avg. Social Welfare: " + str(
    round(averages["social_welfare"] / averages["count"], 2)))

from itertools import permutations
from math import factorial
from typing import Tuple

from geniusweb.profile.utilityspace.LinearAdditiveUtilitySpace import \
    LinearAdditiveUtilitySpace
from geniusweb.profileconnection.ProfileConnectionFactory import \
    ProfileConnectionFactory
from geniusweb.protocol.NegoSettings import NegoSettings
from geniusweb.protocol.session.saop.SAOPState import SAOPState
from geniusweb.simplerunner.ClassPathConnectionFactory import \
    ClassPathConnectionFactory
from geniusweb.simplerunner.NegoRunner import NegoRunner
from pyson.ObjectMapper import ObjectMapper
from uri.uri import URI

from runner.utils.ask_proceed import ask_proceed
from runner.utils.std_out_reporter import StdOutReporter


def run_session(settings):
    agents = settings["agents"]
    profiles = settings["profiles"]
    rounds = settings["deadline_rounds"]

    # quick and dirty checks
    assert isinstance(agents, list) and len(agents) == 2
    assert isinstance(profiles, list) and len(profiles) == 2
    assert isinstance(rounds, int) and rounds > 0

    # file path to uri
    profiles_uri = [f"file:{x}" for x in profiles]

    # create full settings dictionary that geniusweb requires
    settings_full = {
        "SAOPSettings": {
            "participants": [
                {
                    "TeamInfo": {
                        "parties": [
                            {
                                "party": {
                                    "partyref": f"pythonpath:{agents[0]}",
                                    "parameters": {},
                                },
                                "profile": profiles_uri[0],
                            }
                        ]
                    }
                },
                {
                    "TeamInfo": {
                        "parties": [
                            {
                                "party": {
                                    "partyref": f"pythonpath:{agents[1]}",
                                    "parameters": {},
                                },
                                "profile": profiles_uri[1],
                            }
                        ]
                    }
                },
            ],
            "deadline": {"DeadlineRounds": {"rounds": rounds, "durationms": 999}},
        }
    }

    # parse settings dict to settings object
    settings_obj = ObjectMapper().parse(settings_full, NegoSettings)

    # create the negotiation session runner object
    runner = NegoRunner(settings_obj, ClassPathConnectionFactory(), StdOutReporter(), 0)

    # run the negotiation session
    runner.run()

    # get results from the session in class format and dict format
    results_class: SAOPState = runner.getProtocol().getState()
    results_dict = ObjectMapper().toJson(results_class)

    # add utilities to the results and create a summary
    opponent_model, results_trace, results_summary = process_results(results_class, results_dict)

    return opponent_model, results_trace, results_summary


def run_tournament(tournament_settings: dict) -> Tuple[list, list]:
    # create agent permutations, ensures that every agent plays against every other agent on both sides of a profile set.
    agents = tournament_settings["agents"]
    profile_sets = tournament_settings["profile_sets"]
    deadline_rounds = tournament_settings["deadline_rounds"]

    num_sessions = (factorial(len(agents)) // factorial(len(agents) - 2)) * len(profile_sets)
    if num_sessions > 100:
        message = f"WARNING: this would run {num_sessions} negotiation sessions. Proceed?"
        if not ask_proceed(message):
            print("Exiting script")
            exit()

    results_summaries = []
    tournament = []
    for profiles in profile_sets:
        # quick an dirty check
        assert isinstance(profiles, list) and len(profiles) == 2
        for agent_duo in permutations(agents, 2):
            # create session settings dict
            settings = {
                "agents": list(agent_duo),
                "profiles": profiles,
                "deadline_rounds": deadline_rounds,
            }

            # run a single negotiation session
            _, _, results_summary = run_session(settings)

            # assemble results
            tournament.append(settings)
            results_summaries.append(results_summary)

    return tournament, results_summaries


def process_results(results_class, results_dict):
    results_dict = results_dict["SAOPState"]

    # dict to translate geniusweb agent reference to Python class name
    agent_translate = {
        k: v["party"]["partyref"].split(".")[-1]
        for k, v in results_dict["partyprofiles"].items()
    }

    results_summary = {}

    # check if there are any actions (could have crashed)
    if results_dict["actions"]:
        # obtain utility functions
        utility_funcs = {
            k: get_utility_function(v["profile"])
            for k, v in results_dict["partyprofiles"].items()
        }

        # iterate both action classes and dict entries
        actions_iter = zip(results_class.getActions(), results_dict["actions"])

        for num_offer, (action_class, action_dict) in enumerate(actions_iter):
            if "Offer" in action_dict:
                offer = action_dict["Offer"]
            elif "Accept" in action_dict:
                offer = action_dict["Accept"]
            else:
                continue

            # add utility of both agents
            bid = action_class.getBid()
            offer["utilities"] = {
                k: float(v.getUtility(bid)) for k, v in utility_funcs.items()
            }

        results_summary["num_offers"] = num_offer + 1

        # gather a summary of results
        if "Accept" in action_dict:
            for actor, utility in offer["utilities"].items():
                position = actor.split("_")[-1]
                results_summary[f"agent_{position}"] = agent_translate[actor]
                results_summary[f"utility_{position}"] = utility
            util_1, util_2 = offer["utilities"].values()
            results_summary["nash_product"] = util_1 * util_2
            results_summary["social_welfare"] = util_1 + util_2
            results_summary["result"] = "agreement"
        else:
            for actor, utility in offer["utilities"].items():
                position = actor.split("_")[-1]
                results_summary[f"agent_{position}"] = agent_translate[actor]
                results_summary[f"utility_{position}"] = 0
            results_summary["nash_product"] = 0
            results_summary["social_welfare"] = 0
            results_summary["result"] = "failed"
    else:
        # something crashed crashed
        for actor in results_dict["connections"]:
            position = actor.split("_")[-1]
            results_summary[f"agent_{position}"] = agent_translate[actor]
            results_summary[f"utility_{position}"] = 0
        results_summary["nash_product"] = 0
        results_summary["social_welfare"] = 0
        results_summary["result"] = "ERROR"

    # combine expected model with real values
    opponent_model = []
    for action in results_dict["actions"]:
        if "Offer" in action and action["Offer"]["actor"] == "party_Group58_NegotiationAssignment_Agent_1":
            offer = {"issues": action["Offer"]["bid"]["issuevalues"],
                     "utility": action["Offer"]["utilities"][list(action["Offer"]["utilities"])[1]]}

            opponent_model.append(offer)

    with open("OpponentModel.log") as file:
        for i, line in enumerate(file):
            if i < len(opponent_model):
                opponent_model[i]["expected_utility"] = float(line.rstrip())

    return opponent_model, results_dict, results_summary


def get_utility_function(profile_uri) -> LinearAdditiveUtilitySpace:
    profile_connection = ProfileConnectionFactory.create(
        URI(profile_uri), StdOutReporter()
    )
    profile = profile_connection.getProfile()
    assert isinstance(profile, LinearAdditiveUtilitySpace)

    return profile

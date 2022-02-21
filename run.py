import json
import os

import numpy as np
from matplotlib import pyplot as plt

from runner.utils.plot_trace import plot_trace
from runner.utils.runners import run_session

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
    "profiles": ["runner/domains/jobs/jobsprofileA.json", "runner/domains/jobs/jobsprofileB.json"],
    "deadline_rounds": 200,
}

# run a session and obtain results in dictionaries
opponent_model, results_trace, results_summary = run_session(settings)

if len(opponent_model) > 0:
    # plot opponent model vs. real utilities
    fig = plt.gcf()
    x = np.arange(len(opponent_model))
    print()
    print(opponent_model[0])
    real_utilities = np.vectorize(lambda x: x["utility"])(opponent_model)
    moddeled_utilities = np.round(np.vectorize(lambda x: x["expected_utility"])(opponent_model), 3)
    error = np.abs(moddeled_utilities - real_utilities)
    coef = np.polyfit(x, error, 1)
    poly1d_fn = np.poly1d(coef)
    plt.plot(x, real_utilities, c="green", label='Real')
    plt.plot(x, moddeled_utilities, c="red", label='Expected')
    plt.plot(x, poly1d_fn(x), '--k', label='Error')

    plt.xlabel('Rounds')
    plt.ylabel('Utility')
    plt.title('Opponent utility vs. expected utility model')
    plt.legend()
    fig.set_size_inches(20, 10)
    plt.savefig('runner/results/opponent model.png', bbox_inches='tight')

# plot trace to html file
plot_trace(results_trace, "runner/results/trace_plot.html")

# write results to file
with open("runner/results/results_trace.json", "w") as f:
    f.write(json.dumps(results_trace, indent=2))
with open("runner/results/results_summary.json", "w") as f:
    f.write(json.dumps(results_summary, indent=2))

import json
import os

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
results_trace, results_summary = run_session(settings)

# plot trace to html file
plot_trace(results_trace, "runner/results/trace_plot.html")

# write results to file
with open("runner/results/results_trace.json", "w") as f:
    f.write(json.dumps(results_trace, indent=2))
with open("runner/results/results_summary.json", "w") as f:
    f.write(json.dumps(results_summary, indent=2))

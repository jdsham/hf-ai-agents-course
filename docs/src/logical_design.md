## The Orchestrator
The orchestrator node is hard-coded logic to determine the flow control of the graph.
It keeps track of the overall process by knowing the current step when the node is activated and determines the next step.
The steps are the other nodes in the graph.
Note that the orchestrator is not a step on purpose, and the other nodes (except the finalizer) will connect back to the orchestrator agent.
The graph steps are:
- input: this signifies the start of the graph and will be the default value the orchestrator sees. It will never be set this value again.
- planner: invoke the planning agent
- critic_planner: invoke the critic for the planning agent
- researcher: invoke the researcher agent
- critic_researcher: invoke the critic for the researcher agent
- expert: invoke the expert agent
- critic_expert: invoke the critic for the expert agent
- finalizer: invoke the finalizer agent to generate the final answer and reasoning trace

The orchestrator also keeps track of the retry count, and will break the graph cycle if the retry count reaches the retry limit.

It will perform the following logical tasks in order:

1. Determine the next step
    - Use the current step and other graph state variables when needed
    - Also increment the retry count when a critic decision is a rejection.

2. Check the retry count.
    - If retry count >= retry limit: set the next step for finalizer. Set the final answer and reasoning trace as "I could not answer the question."
    - Otherwise, do nothing.

3. Do the next step
    - Set the current step = next step
    - Set next step as empty string?
    - Send message to the agent being called in the new current step.

4. Return state



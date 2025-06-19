
from google.adk.agents import SequentialAgent              
from .planner_agent.planner          import planner_agent
from .guard_agent.guard              import guard_agent
from .worker_hub_agent.worker_hub    import worker_hub

# The SequentialAgent will simply run Planner ➜ (others invoked via ToolCalls)
root_agent = SequentialAgent(
    name="RootCoordinator",
    sub_agents=[
        planner_agent,
        guard_agent,
        worker_hub,
    ],
)
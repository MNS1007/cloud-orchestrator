from google.adk.agents import SequentialAgent              
from .planner_agent.agent          import root_agent as PlannerAgent
from .guard_agent.guard              import guard_agent as GuardAgent
from .worker_hub_agent.agent    import root_agent as WorkerHubAgent

# The SequentialAgent will simply run Planner ➜ (others invoked via ToolCalls)
root_agent = SequentialAgent(
    name="RootCoordinator",
    sub_agents=[
        PlannerAgent,
        GuardAgent,
        WorkerHubAgent,
    ],
)
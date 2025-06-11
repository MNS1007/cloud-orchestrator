
from google.adk.agents import SequentialAgent              
from .planner_agent.planner          import PlannerAgent
from .guard_agent.guard              import GuardAgent
from .worker_hub_agent.worker_hub    import worker_hub

# The SequentialAgent will simply run Planner ➜ (others invoked via ToolCalls)
root_agent = SequentialAgent(
    name="RootCoordinator",
    sub_agents=[
        PlannerAgent(name="Planner"),
        GuardAgent(name="Guard"),
        worker_hub,
    ],
)
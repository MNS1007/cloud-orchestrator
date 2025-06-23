from google.adk.agents import Agent
from .planner_agent import planner_agent
from .guard_agent   import guard_agent
from .worker_hub    import worker_hub_agent

root_agent = Agent(
    name         = "cloud_orchestrator_root",
    model        = "gemini-2.5-flash",
    global_instruction = (
        "You are the conductor. Take a user request → "
        "let PlannerAgent devise the DAG, GuardAgent approve budgets, "
        "WorkerHub execute. Summarise when done."
    ),
    sub_agents   = [planner_agent, guard_agent, worker_hub_agent],
)
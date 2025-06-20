from google.adk.agents import Agent
from .tools.planner_tool import (
    open_dag_page,
    parse_user_goal,
    build_service_dag,
    expand_to_tool_plan,
)

# Ensure dependencies are installed before running:
# python3 -m pip install matplotlib networkx

root_agent = Agent(
    name="planner_agent_v1",
    model="gemini-2.5-flash",
    description="GCP Planner – intent→service DAG→tool plan (phase 1‑3 completed)",
    instruction=(
        "You are a planning orchestrator. Steps:\n"
        "1. Call parse_user_goal(prompt).\n"
        "2. Feed its output into build_service_dag().\n"
        "3. Feed that DAG into expand_to_tool_plan().\n"
        "4. Use open_dag_page() to visualize the DAG.\n"
        "5. Return ONLY the output of expand_to_tool_plan().\n"
        "If any step returns an error key, stop and return it."
    ),
    tools=[
        parse_user_goal,
        build_service_dag,
        expand_to_tool_plan,
        open_dag_page,
    ],
)

print(f"✅ Planner Agent '{root_agent.name}' initialized")

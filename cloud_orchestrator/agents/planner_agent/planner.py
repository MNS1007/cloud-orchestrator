# python3 -m pip install matplotlib networkx
from google.adk.agents import Agent
from .tools.planner_tool import build_dag_from_prompt

planner_agent = Agent(
    name="planner_agent_v1",
    model="gemini-2.5-flash",
    description="Parses instructions and builds a DAG of GCP services required to fulfill a cloud infrastructure task.",
    instruction=(
        "You are a GCP planning assistant. When given a user instruction:\n"
        "1. Call the tool 'build_dag_from_prompt' exactly once with the user instruction as input.\n"
        "2. Return only the output of the tool as your final answer.\n"
        "3. Do not attempt to interpret or modify the tool's output.\n"
        "4. If the tool returns an error (e.g., a dictionary with the key 'error'), immediately stop and return that error message.\n\n"
        "Never call the tool recursively or more than once. Do not rephrase the instruction or retry on your own.\n"
        "Do not generate explanations, summaries, or any other output — just relay the tool's return value."
    ),
    tools=[
        build_dag_from_prompt
    ]
)

print(f"✅ Planner Agent '{planner_agent.name}' created using model gemini-2.0-flash")
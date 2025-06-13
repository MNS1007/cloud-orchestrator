

from google.adk.agents import Agent
from .tools import cloudmonitoring    

cloudmonitoring_agent = Agent(
    name="cloudmonitoring_agent",
    model="gemini-2.0-flash",
    description="Creates dashboards and alerting policies in Cloud Monitoring",
    instruction="""You are a specialised Cloud-Monitoring assistant.
• If the user asks for a dashboard, call `create_dashboard`.
• If the user asks for an alerting policy, call `create_alert`.
• After executing the tool, confirm success and give the resource name.
""",
    tools=[*cloudmonitoring.get_tools()]  
)


root_agent = Agent(
    name="worker_hub_agent",
    model="gemini-2.0-flash",
    global_instruction="You are the Worker-Hub for GCP operations.",
    instruction="""Handle Cloud Monitoring requests yourself or pass them
to the cloudmonitoring_agent when appropriate.
When the sub-agent finishes, ask the user if they need anything else.""",
    sub_agents=[cloudmonitoring_agent],
    tools=[*cloudmonitoring.get_tools()],    
)
from google.adk.agents import Agent
from .tools import cloudmonitoring, secret_manager      
from .tools.cloud_sql_fix import *  

cloudmonitoring_agent = Agent(
    name="cloudmonitoring_agent",
    model="gemini-2.0-flash",
    description="Creates dashboards and alert policies",
    instruction="""If the user mentions dashboards or alerts, call the matching
tool (`create_dashboard`, `create_alert`), then confirm with the resource name.""",
    tools=[*cloudmonitoring.get_tools()],
)

secretmanager_agent = Agent(
    name="secretmanager_agent",
    model="gemini-2.0-flash",
    description="Manages secrets and versions",
    instruction="""If the user asks to store a secret or add a new version,
use `create_secret` or `add_version`. Return the Secret resource name.""",
    tools=[*secret_manager.get_tools()],
)

cloud_sql_agent = Agent(
    name = "cloud_sql_agent",
    model = "gemini-2.5-flash",
    description= "Executes PSQL Query",
    instruction= "Use 'run_psql_query' when the user wants to run a SQL query on a Cloud SQL instance. If it is a select query then display the output.\n",
    tools=[run_psql_query],
)

root_agent = Agent(
    name="worker_hub_agent",
    model="gemini-2.0-flash",
    global_instruction="You are the Worker-Hub for GCP operations.",
    instruction="""Handle Cloud Monitoring or Secret-Manager requests yourself,
or delegate to the appropriate sub-agent. After each task, ask if the user needs
anything else.""",
    sub_agents=[cloudmonitoring_agent, secretmanager_agent,cloud_sql_agent],
    tools=[*cloudmonitoring.get_tools(), *secret_manager.get_tools(),run_psql_query],
)
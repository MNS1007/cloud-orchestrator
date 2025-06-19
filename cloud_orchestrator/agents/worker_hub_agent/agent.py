#Root Agent

from google.adk.agents import Agent
from .tools import vpc, firestore


vpc_agent = Agent(
    name="vpc_agent",
    model="gemini-2.0-flash",
    description="Handles Google Cloud VPC networking tasks such as creating networks, managing subnets, and checking connectivity.",
    instruction="""
        You are a GCP networking assistant. Your job is to help users manage VPC networks and subnets on Google Cloud 
        by calling the appropriate tools based on user intent.

        Use the tools as follows:
        - Use `manage_vpc_network` to check if a VPC exists, create one if it doesn't, and optionally create subnets.
        - Use `check_network_subnets` to verify if subnets belong to the same network and can communicate.

        Always infer user intent from natural language. Ask for missing inputs such as:
        - VPC name
        - Project ID
        - Whether they want to create subnets
        - Subnet definitions (name, region, IP range)

        If a tool fails, explain the error clearly and guide the user to correct the inputs or retry. 
        Ensure a smooth, step-by-step experience for the user when gathering required information.
    """,
    tools=[*vpc.get_tools()],
)


firestore_agent = Agent(
    name="firestore_agent",
    model="gemini-2.0-flash",
    description="Helps users create Firestore databases, add documents, and configure TTL policies.",
    instruction="""
        You are a Firestore assistant. You help users:
        - Create Firestore databases
        - Add documents to collections
        - Set TTL policies for document expiration

        Use these tools:
        - `create_firestore_db` to create or check a Firestore database, and to add documents.
        - `set_ttl` to configure a TTL field for automatic expiration.

        When adding documents, ask for:
        - Collection name
        - Document data (list of dictionaries with optional 'doc_id')

        When setting TTL, ask for:
        - project_id
        - db_name
        - collection_name
        - ttl_field

        If the TTL field is missing or invalid, ask how many days from now documents should expire (`ttl_days`).

        Always infer user intent from natural language and ask for any missing inputs.
        If a tool fails, explain the error clearly and guide the user to fix it.
    """,
    tools=[*firestore.get_tools()],
)


root_agent = Agent(
    name="worker_hub_agent",
    model="gemini-2.0-flash",
    global_instruction="You are the Worker-Hub for GCP operations.",
    instruction="""Handle VPC network or Firestore database requests yourself,
    or delegate to the appropriate sub-agent. After each task, ask if the user needs
    anything else.""",
    sub_agents=[vpc_agent, firestore_agent],
    tools=[*vpc.get_tools(), *firestore.get_tools()],
)

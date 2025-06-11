# brew install --cask google-cloud-sdk
# export PATH="$PATH:/opt/homebrew/bin"
# python3 -m pip install google-adk
# export PATH="$HOME/Library/Python/3.9/bin:$PATH"

from google.adk.agents import Agent
from .tools.iam import create_sa, grant_role
from .tools.bigquery import create_dataset, create_table, insert_json


worker_hub = Agent(
    name="worker_hub_v1",
    model="gemini-2.0-flash",
    description="Handles GCP cloud tasks such as IAM, BigQuery and compute setup.",
    instruction=(
        "You are a GCP infrastructure assistant. Your job is to help users manage their Google Cloud Platform resources "
        "by calling the appropriate tools.\n\n"
        "- Use 'create_sa' when the user wants to create a new service account (usually for Pub/Sub).\n"
        "- Use 'grant_role' when the user wants to assign a role (e.g., Pub/Sub viewer, Cloud Functions invoker) to a user, group, or service account.\n"
        "- Use 'create_dataset' when the user asks to create a new BigQuery dataset in a specific location.\n"
        "- Use 'create_table' when the user wants to create a table inside a dataset, with a provided schema.\n"
        "- Use 'insert_json' when the user wants to insert rows of data (in JSON format) into a BigQuery table.\n\n"
        "Always infer intent from natural language and call the right tool. If a tool fails, clearly explain what went wrong and suggest how to fix it if possible."
    ),
    tools=[
        create_sa,
        grant_role,
        create_dataset,
        create_table,
        insert_json,
    ],
)

print(f"✅ Agent '{worker_hub.name}' created using model gemini-2.0-flash")

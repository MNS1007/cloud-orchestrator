# brew install --cask google-cloud-sdk
# export PATH="$PATH:/opt/homebrew/bin"
# python3 -m pip install google-adk
# export PATH="$HOME/Library/Python/3.9/bin:$PATH"
# python3 -m pip install google-generativeai

from google.adk.agents import Agent
from .tools.iam import create_sa, grant_role, delete_sa
from .tools.bigquery import create_dataset, create_table, insert_json, export_table_gcs
from .tools.pubsub import create_topic, create_subscription, publish, pull
from .tools.computeengine import create_vm, delete_vm, get_external_ip, snapshot_disk
from .tools.dataflow import launch_flex_template, monitor_job, cancel_job, list_jobs

worker_hub = Agent(
    name="worker_hub_v1",
    model="gemini-2.0-flash",
    description="Handles GCP cloud tasks such as IAM, BigQuery, and Pub/Sub setup.",
    instruction=(
        "You are a GCP infrastructure assistant. Your job is to help users manage their Google Cloud Platform resources "
        "by calling the appropriate tools.\n\n"
        "- Use 'create_sa' when the user wants to create a new service account (usually for Pub/Sub).\n"
        "- Use 'grant_role' when the user wants to assign a role (e.g., Pub/Sub viewer, Cloud Functions invoker) to a user, group, or service account.\n"
        "- Use 'delete_sa' when the user wants to delete a service account.\n"
        "- Use 'create_dataset' when the user asks to create a new BigQuery dataset in a specific location.\n"
        "- Use 'create_table' when the user wants to create a table inside a dataset, with a provided schema.\n"
        "- Use 'insert_json' when the user wants to insert rows of data (in JSON format) into a BigQuery table.\n"
        "- Use 'export_table_gcs' when the user wants to export a BigQuery table to Google Cloud Storage.\n"
        "- Use 'create_topic' to create a new Pub/Sub topic.\n"
        "- Use 'create_subscription' to create a subscription for a given topic.\n"
        "- Use 'publish' to publish a message to a Pub/Sub topic.\n"
        "- Use 'pull' to pull messages from a Pub/Sub subscription.\n"
        "- Use 'create_vm' to provision a new Compute Engine VM.\n"
        "- Use 'delete_vm' to delete an existing VM.\n"
        "- Use 'get_external_ip' to retrieve the external IP address of a VM.\n\n"
        "- Use 'snapshot_disk' to create a snapshot of a Compute Engine persistent disk.\n\n"
        "- Use 'launch_flex_template' to run a Dataflow job from a Flex Template.\n"
        "- Use 'monitor_job' to check the current status of a Dataflow job.\n\n"
        "- Use 'cancel_job' to cancel a running Dataflow job.\n"
        "- Use 'list_jobs' to list recent Dataflow jobs in a given region.\n\n"
        "Always infer intent from natural language and call the right tool. If a tool fails, clearly explain what went wrong and suggest how to fix it if possible."
    ),
    tools=[
        create_sa,
        grant_role,
        delete_sa,
        create_dataset,
        create_table,
        insert_json,
        export_table_gcs,
        create_topic,
        create_subscription,
        publish,
        pull,
        create_vm,
        delete_vm,
        get_external_ip,
        snapshot_disk,
        launch_flex_template,
        monitor_job,
        cancel_job,
        list_jobs,
    ],
)


print(f"✅ Agent '{worker_hub.name}' created using model gemini-2.0-flash")

#Root Agent

from google.adk.agents import Agent
from .tools import vpc, firestore, cloudrun, dataproc


vpc_agent = Agent(
    name="vpc_agent",
    model="gemini-2.0-flash",
    description=(
        "Assists users in managing VPC networks on Google Cloud. "
        "Supports creating networks, adding subnets, and checking subnet connectivity."
    ),
    instruction="""
        You are a GCP VPC networking assistant. Your job is to guide users through:
        - Creating or checking VPC networks
        - Adding subnets to a VPC
        - Checking if subnets belong to the same network

        Use the tool `manage_vpc_network` to:
        - Check if a VPC exists
        - Create a VPC if it does not exist
        - Optionally create subnets after VPC creation or if VPC already exists
        - Ask the user for:
          - VPC name
          - Project ID
          - Whether they want to create subnets
          - Subnet definitions (list of name, region, and IP range)

        Use the tool `check_network_subnets` to:
        - Check if subnets belong to the same VPC network
        - Ask the user for:
          - Subnet names and their regions
          - Project ID

        Always infer user intent from natural language.
        If any required input is missing, prompt the user for them.

        If an operation fails, explain the error clearly and suggest possible fixes.
        Guide the user step-by-step to ensure a successful setup.
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

        Some documents may already have TTL , that time you should not ask for days or field , if it doesnt have TTL then you should ask the field and if the field is expiresAt then you should ask for days (`ttl_days`)

        Always infer user intent from natural language and ask for any missing inputs.
        If a tool fails, explain the error clearly and guide the user to fix it.
    """,
    tools=[*firestore.get_tools()],
)


cloudrun_agent = Agent(
    name="cloudrun_agent",
    model="gemini-2.0-flash",
    description=(
        "Helps deploy and manage services on Google Cloud Run. "
        "Supports Docker builds, Git source deployments, Cloud Functions, "
        "env updates, service pause, and deletion."
    ),
    instruction="""
        You are a Cloud Run deployment assistant for Google Cloud Platform (GCP). 
        Your job is to help users with:

        - Deploying services (Docker, Git source, or Cloud Function)
        - Updating environment variables
        - Pausing services
        - Deleting services

         Use `create_service` to:
        - Deploy services to Cloud Run or Cloud Functions
        - Ask for: 
          - service name
          - service type: must be "docker", "git", or "function"
          - image or source path
          - region (default: us-central1)
          - project ID
          - runtime and entry point (for functions)

         Use `update_env` to:
        - Add or change environment variables on a deployed service
        - Ask for: service name, region, env vars, and (for functions) source directory

         Use `pause_service` to:
        - Route 0% traffic to pause a Cloud Run service
        - Ask for: service name, region, and project ID

         Use `delete_service` to:
        - Delete a deployed Cloud Run service
        - Ask for: service name, region, and project ID

        Always mention what service types are available when you ask the user for service_type - 'docker or git ot function'

        Always infer intent from natural language.
        If inputs are missing, prompt the user clearly. 
        If something fails, explain the issue and suggest fixes.
    """,
    tools=[*cloudrun.get_tools()]
)

dataproc_agent = Agent(
    name="dataproc_agent",
    model="gemini-2.0-flash",
    description=(
        "Assists users in creating and deleting clusters on Google Cloud Dataproc, "
        "and running PySpark jobs. Supports enabling APIs, provisioning and deleting clusters, "
        "and submitting PySpark jobs with optional input/output parameters."
    ),
    instruction="""
        You are a GCP Dataproc assistant. Your job is to guide users through:

        - Creating Dataproc clusters with required settings
        - Deleting Dataproc clusters safely
        - Running PySpark jobs on Dataproc clusters with optional input/output arguments

        Use the tool `create_cluster` to:
        - Provision a new Dataproc cluster with a specified number of worker nodes
        - Automatically enable the Dataproc API if needed
        - Ask the user for:
          - Cluster name
          - Region
          - Number of worker nodes
          - GCP project ID

        Use the tool `delete_cluster` to:
        - Delete an existing Dataproc cluster
        - Automatically ensure the Dataproc API is enabled
        - Ask the user for:
          - Cluster name
          - Region
          - GCP project ID
        - Warn the user that deletion is irreversible and may result in data loss

        Use the tool `run_pyspark` to:
        - Submit PySpark jobs to an existing Dataproc cluster
        - Ask the user for:
          - Bucket name
          - Cluster name
          - Project ID
          - Region
          - Optional input file path
          - Optional output folder path
        - Warn the user if input/output files/folders are not provided and might be required by the script

        Always infer user intent from natural language.
        If any required input is missing, prompt the user for it.

        If any operation fails, explain the error clearly and suggest possible fixes.
        Guide the user step-by-step to ensure successful cluster setup, deletion, or job submission.
    """,
    tools=[*dataproc.get_tools()]  # Ensure `delete_cluster` is included in get_tools()
)


root_agent = Agent(
    name="worker_hub_agent",
    model="gemini-2.0-flash",
    global_instruction="You are the Worker-Hub for GCP operations.",
    instruction="""Handle VPC network or Firestore database or Cloud Run service or Dataproc requests yourself,
    or delegate to the appropriate sub-agent. After each task, ask if the user needs
    anything else.""",
    sub_agents=[vpc_agent, firestore_agent],
    tools=[*vpc.get_tools(), *firestore.get_tools(), *cloudrun.get_tools(), *dataproc.get_tools()],
)

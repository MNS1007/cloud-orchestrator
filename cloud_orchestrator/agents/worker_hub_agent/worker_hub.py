from google.adk.agents import Agent
from .tools.iam import *
from .tools.cloud_storage import *
# from .tools.cloud_storage_notSmartYet import gcloud_task
from .tools.cloud_sql import *
from .tools.cloud_logging import *
from .tools.cloud_build import *
from .tools.cloud_artifacts import *

worker_hub = Agent(
    name="worker_hub_v1",
    model="gemini-2.0-flash",
    description="Handles GCP cloud tasks such as IAM, BigQuery, Cloud Storage, Cloud SQL and compute setup.",
    instruction=(
        "You are a GCP infrastructure assistant. Your job is to help users manage their Google Cloud Platform resources "
        "by calling the appropriate tools.\n\n"

        # cloud iam
        "- Use 'create_sa' when the user wants to create a new service account (usually for Pub/Sub).\n"
        "- Use 'grant_role' when the user wants to assign a role (e.g., Pub/Sub viewer, Cloud Functions invoker) to a user, group, or service account.\n"
        
        # big query
        "- Use 'create_dataset' when the user asks to create a new BigQuery dataset in a specific location.\n"
        "- Use 'create_table' when the user wants to create a table inside a dataset, with a provided schema.\n"
        "- Use 'insert_json' when the user wants to insert rows of data (in JSON format) into a BigQuery table.\n\n"
        
        # cloud storage
        "- Use 'create_bucket' when the user wants to create a new Cloud Storage bucket.\n"
        "- Use 'enable_versioning' when the user wants to enable versioning on an existing bucket.\n"
        "- Use 'upload_to_bucket' when the user wants to upload a file to a bucket.\n"
        "- Use 'set_default_storage_class' when the user wants to set the default storage class for a bucket.\n"
        "- Use 'enable_soft_delete' when the user wants to enable soft delete on a bucket.\n"
        "- Use 'enable_autoclass' when the user wants to enable autoclass on a bucket.\n"
        "- Use 'set_uniform_access' when the user wants to set uniform access on a bucket.\n"
        "- Use 'set_lifecycle_rule' when the user wants to set a lifecycle rule on a bucket.\n"
        # "- Use 'gcloud_task' when the user wants to perform a Cloud Storage action.\n"

        # cloud sql
        # Utility / Custom Operations
        "- Use 'run_psql_query' when the user wants to run a SQL query on a Cloud SQL instance. If it is a select query then display the output.\n"
        # # Section 1 : Managing Instances
        # "- Use 'create_sql_instance' when the user wants to create a new Cloud SQL instance.\n"
        # "- Use 'describe_sql_instance' when the user wants to view detailed info about a specific instanc.\n"
        # "- Use 'list_sql_instances' when the user wants to list all SQL instances in the project.\n"
        # "- Use 'delete_sql_instance' when the user wants to permanently delete a Cloud SQL instance.\n"
        # "- Use 'update_sql_instance' when the user wants to modify the configuration of an instance.\n"
        # "- Use 'restart_sql_instance' when the user wants to restart an existing Cloud SQL instance.\n"
        # "- Use 'connect_to_sql_instance' when the user wants to connect to a Cloud SQL instance via psql.\n"
        # "- Use 'reschedule_sql_maintenance' when the user wants to change the scheduled maintenance window for an instance.\n"
        # # Section 2: Managing Databases
        # "- Use 'create_sql_database' when the user wants to create a new database within a Cloud SQL instance.\n"
        # "- Use 'describe_sql_database' when the user wants to view configuration info for a specific database.\n"
        # "- Use 'list_sql_databases' when the user wants to list all databases in a specific instance.\n"
        # "- Use 'delete_sql_database' when the user wants to delete a specific database.\n"
        # "- Use 'patch_sql_database' when the user wants to update database settings like collation or charset.\n"
        # # Section 3: Managing Users
        # "- Use 'create_sql_user' when the user wants to create a new database user.\n"
        # "- Use 'delete_sql_user' when the user wants to remove an existing database user.\n"
        # "- Use 'list_sql_users' when the user wants to list all users for an instance.\n"
        # "- Use 'set_sql_password' when the user wants to change the password for a specific SQL user.\n"
        # # Section 4 : Managing Backups
        # "- Use 'create_sql_backup' when the user wants to create an on-demand backup of an instance.\n"
        # "- Use 'delete_sql_backup' when the user wants to delete a specific backup by ID.\n"
        # "- Use 'describe_sql_backup' when the user wants to view details about a specific backup.\n"
        # "- Use 'list_sql_backups' when the user wants to list all backups for an instance.\n"
        # "- Use 'restore_sql_instance' when the user wants to restore a Cloud SQL instance from a specific backup.\n"
        # # Section 5 : Importing & Exporting Data
        # "- Use 'export_sql_data' when the user wants to export SQL data to a Cloud Storage bucket.\n"
        # "- Use 'import_sql_data' when the user wants to import SQL data from a Cloud Storage bucket into an instance.\n"
        # # Section 6 : Managing SSL Certificates
        # "- Use 'create_sql_ssl_cert' when the user wants to generate a new SSL certificate for secure connections.\n"
        # "- Use 'delete_sql_ssl_cert' when the user wants to remove an existing SSL certificate.\n"
        # "- Use 'describe_sql_ssl_cert' when the user wants to view details of an SSL certificate.\n"
        # "- Use 'list_sql_ssl_certs' when the user wants to list all SSL certificates for an instance.\n"
        # # Section 7 : Monitoring Operations
        # "- Use 'list_sql_operations' when the user wants to view recent operations on an instance (e.g. creation, update, backup).\n"
        # # Section 8 : Miscellaneous Tools
        # "- Use 'list_sql_tiers' when the user wants to view all available machine tiers (CPU/memory configs).\n"
        # "- Use 'list_sql_flags' when the user wants to see configurable flags for Cloud SQL instances.\n"
        # "- Use 'generate_sql_login_token' when the user wants to generate a temporary IAM token to log in securely.\n"

        # cloud logging
        "- Use 'write_custom_log_entry' to write a custom log entry using gcloud CLI."
        "- Use 'create_log_based_metric' to create a log-based counter metric using a filter on textPayload."
        "- USe 'describe_log_based_metric' to describe a previously created log-based metric."

        # cloud build 
        "- Use 'enable_cloud_build_api' to enable the cloud build api"
        "- Use 'configure_docker_auth' to cinfure docker"
        "- Use 'build_and_push_docker_image' to build and push docker image"

        # artifact registry
        "- Use 'enable_artifact_registry_api' to enable the artifact registry api"
        "- Use 'create_docker_repository' to create docker repository"

        "Always infer intent from natural language and call the right tool. If a tool fails, clearly explain what went wrong and suggest how to fix it if possible."
    ),
    tools=[
        # cloud iam
        create_sa,
        grant_role,

        # cloud storage
        create_bucket,
        enable_versioning,
        upload_to_bucket,
        set_default_storage_class,
        enable_soft_delete,
        enable_autoclass,
        set_uniform_access,
        set_lifecycle_rule,
        # gcloud_task - not smart yet

        # cloud sql
        # create_sql_instance,
        # describe_sql_instance,
        # list_sql_instances,
        # delete_sql_instance,
        # update_sql_instance,
        # restart_sql_instance,
        # connect_to_sql_instance,
        # reschedule_sql_maintenance,

        # create_sql_database,
        # describe_sql_database,
        # list_sql_databases,
        # delete_sql_database,
        # patch_sql_database,

        # create_sql_user,
        # delete_sql_user,
        # list_sql_users,
        # set_sql_password,

        # create_sql_backup,
        # delete_sql_backup,
        # describe_sql_backup,
        # list_sql_backups,
        # restore_sql_instance,

        # export_sql_data,
        # import_sql_data,

        # create_sql_ssl_cert,
        # delete_sql_ssl_cert,
        # describe_sql_ssl_cert,
        # list_sql_ssl_certs,

        # list_sql_operations,

        # list_sql_tiers,
        # list_sql_flags,
        # generate_sql_login_token,

        run_psql_query,

        # cloud logging
        write_custom_log_entry,
        create_log_based_metric,
        describe_log_based_metric,

        # cloud build
        enable_cloud_build_api,
        configure_docker_auth,
        build_and_push_docker_image,

        # artifact registry
        enable_artifact_registry_api,
        create_docker_repository
        
    ],
)

print(f"✅ Agent '{worker_hub.name}' created using model gemini-2.0-flash")



# from google.adk.agents import Agent
# import importlib, inspect

# class WorkerHubAgent(Agent):
#     def __init__(self, name: str):
#         super().__init__(
#             name=name,
#             description="Worker hub agent that handles cloud operations"
#         )
    
#     def __getattr__(self, attr):
#         if "_" not in attr:
#             raise AttributeError(attr)
#         service, fn = attr.split("_", 1)
#         try:
#             mod = importlib.import_module(f".tools.{service}", package=__package__)
#             tool_fn = getattr(mod, fn)
#             if not inspect.isfunction(tool_fn):
#                 raise AttributeError(attr)
#             return tool_fn
#         except (ImportError, AttributeError) as e:
#             raise AttributeError(f"Tool {attr} not found: {str(e)}")

# brew install --cask google-cloud-sdk
# export PATH="$PATH:/opt/homebrew/bin"
# python3 -m pip install google-adk
# export PATH="$HOME/Library/Python/3.9/bin:$PATH"
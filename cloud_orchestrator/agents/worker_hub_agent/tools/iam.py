import subprocess
import datetime
from google.adk.tools.function_tool import FunctionTool

@FunctionTool
def create_sa(project_id: str, display_name: str = "Pub/Sub Service Account") -> dict:
    """Create a service account and bind Pub/Sub Publisher role to it."""
    
    try:
        # Generate a unique service account name if not provided
        
        sa_name = f"pubsub-sa-SWAPNITA011"

        sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"

        # Step 0: Enable necessary APIs
        subprocess.run([
            "gcloud", "services", "enable", "iam.googleapis.com", "--project", project_id
        ], check=True)
        subprocess.run([
            "gcloud", "services", "enable", "pubsub.googleapis.com", "--project", project_id
        ], check=True)

        # Step 1: Create the service account
        subprocess.run([
            "gcloud", "iam", "service-accounts", "create", sa_name,
            "--description=Publishes messages to Pub/Sub",
            f"--display-name={display_name}",
            "--project", project_id
        ], check=True)

        # Step 2: Bind the Pub/Sub Publisher role
        subprocess.run([
            "gcloud", "projects", "add-iam-policy-binding", project_id,
            f"--member=serviceAccount:{sa_email}",
            "--role=roles/pubsub.publisher"
        ], check=True)

        return {
            "message": f"✅ Service account '{sa_email}' created and granted 'roles/pubsub.publisher'."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Command failed with return code {e.returncode}. Details:\n{e}"
        }

@FunctionTool
def grant_role(project_id: str, member: str, role: str) -> dict:
    """
    Grants an IAM role to a member (e.g., service account, user, or group) in the given project.

    Parameters:
    - project_id: GCP project ID
    - member: IAM identity (e.g., serviceAccount:name@project.iam.gserviceaccount.com, user:email, group:email)
    - role: IAM role to grant (e.g., roles/pubsub.publisher)
    """
    try:
        # Step 0: Enable necessary APIs
        subprocess.run([
            "gcloud", "services", "enable", "iam.googleapis.com", "--project", project_id
        ], check=True)
        subprocess.run([
            "gcloud", "services", "enable", "pubsub.googleapis.com", "--project", project_id
        ], check=True)
        subprocess.run([
            "gcloud", "projects", "add-iam-policy-binding", project_id,
            f"--member={member}",
            f"--role={role}"
        ], check=True)

        return {
            "message": f"✅ Role '{role}' successfully granted to '{member}' in project '{project_id}'."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to grant role. Details:\n{e}"
        }
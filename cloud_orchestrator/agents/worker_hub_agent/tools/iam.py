import subprocess
from google.adk.tools.function_tool import FunctionTool

@FunctionTool
def create_sa(project_id: str, display_name: str = "Pub/Sub Service Account") -> dict:
    """Create a service account and bind Pub/Sub Publisher role to it."""
    try:
        sa_name = "super-boy"
        sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
        print("check-1 : ", sa_name)

        # Step 0: Check gcloud version (just to verify gcloud is working)
        subprocess.run("gcloud --version", shell=True, check=True)
        print("check-2: passed")

        # Enable necessary APIs
        subprocess.run(
            f"gcloud services enable iam.googleapis.com --project {project_id}",
            shell=True,
            check=True,
        )
        print("check-3: passed")

        subprocess.run(
            f"gcloud services enable pubsub.googleapis.com --project {project_id}",
            shell=True,
            check=True,
        )
        print("check-4: passed")
        

        # Step 1: Create the service account
        subprocess.run(
            f'gcloud iam service-accounts create {sa_name} '
            f'--description="Publishes messages to Pub/Sub" '
            f'--display-name="{display_name}" '
            f'--project {project_id}',
            shell=True,
            check=True,
        )
        print("check-5: passed")
        # Step 2: Bind the Pub/Sub Publisher role
        subprocess.run(
            f"gcloud projects add-iam-policy-binding {project_id} "
            f"--member=serviceAccount:{sa_email} "
            f"--role=roles/pubsub.publisher",
            shell=True,
            check=True,
        )
        print("check-6: passed")

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
    """
    try:
        # Enable necessary APIs
        subprocess.run(
            f"gcloud services enable iam.googleapis.com --project {project_id}",
            shell=True,
            check=True,
        )
        subprocess.run(
            f"gcloud services enable pubsub.googleapis.com --project {project_id}",
            shell=True,
            check=True,
        )
        subprocess.run(
            f"gcloud projects add-iam-policy-binding {project_id} "
            f"--member={member} "
            f"--role={role}",
            shell=True,
            check=True,
        )

        return {
            "message": f"✅ Role '{role}' successfully granted to '{member}' in project '{project_id}'."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to grant role. Details:\n{e}"
        }

import subprocess
from google.adk.tools.function_tool import FunctionTool

@FunctionTool
def launch_flex_template(project_id: str, region: str, job_name: str, template_path: str, parameters: dict) -> dict:
    """
    Launch a Dataflow job using a Flex Template.
    - template_path: GCS path to the Flex Template spec (e.g., gs://my-bucket/templates/my-job.json)
    - parameters: Dictionary of key-value pairs required by the template
    """
    try:
        cmd = [
            "gcloud", "dataflow", "flex-template", "run", job_name,
            f"--project={project_id}",
            f"--region={region}",
            f"--template-file-gcs-location={template_path}",
            "--parameters=" + ",".join(f"{k}={v}" for k, v in parameters.items())
        ]

        subprocess.run(cmd, check=True)
        return {
            "message": f"✅ Dataflow Flex Template '{job_name}' launched successfully in region '{region}'."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to launch Flex Template. Details:\n{e}"
        }


@FunctionTool
def monitor_job(project_id: str, region: str, job_id: str) -> dict:
    """Monitor the status of a running Dataflow job."""
    try:
        result = subprocess.run([
            "gcloud", "dataflow", "jobs", "describe", job_id,
            f"--project={project_id}",
            f"--region={region}",
            "--format=value(currentState)"
        ], check=True, capture_output=True, text=True)

        return {
            "status": result.stdout.strip()
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to monitor Dataflow job. Details:\n{e}"
        }

@FunctionTool
def cancel_job(project_id: str, region: str, job_id: str) -> dict:
    """Cancel a running Dataflow job."""
    try:
        result = subprocess.run([
            "gcloud", "dataflow", "jobs", "cancel", job_id,
            f"--project={project_id}",
            f"--region={region}"
        ], check=True, capture_output=True, text=True)

        return {
            "message": f"🛑 Job {job_id} cancelled successfully.",
            "output": result.stdout.strip()
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to cancel job {job_id}. Details:\n{e}"
        }

@FunctionTool
def list_jobs(project_id: str, region: str, limit: int = 5) -> dict:
    """List recent Dataflow jobs in a region."""
    try:
        result = subprocess.run([
            "gcloud", "dataflow", "jobs", "list",
            f"--project={project_id}",
            f"--region={region}",
            f"--limit={limit}",
            "--format=value(id,name,currentState,creationTime)"
        ], check=True, capture_output=True, text=True)

        jobs = [
            dict(zip(["job_id", "name", "status", "created"], line.split('\t')))
            for line in result.stdout.strip().splitlines()
        ]

        return {
            "jobs": jobs
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to list jobs. Details:\n{e}"
        }
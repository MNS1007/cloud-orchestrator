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

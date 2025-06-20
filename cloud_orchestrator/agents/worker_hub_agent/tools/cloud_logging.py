import subprocess
from google.adk.tools.function_tool import FunctionTool

@FunctionTool
def write_custom_log_entry(log_name: str, message: str, severity: str = "INFO") -> dict:
    """
    Writes a custom log entry using gcloud CLI.
    """
    try:
        result = subprocess.run(
            f'gcloud logging write {log_name} "{message}" --severity={severity}',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return {"message": "✅ Log entry created.", "stdout": result.stdout}
        else:
            return {"error": "❌ Failed to create log entry.", "stderr": result.stderr}
    except Exception as e:
        return {"error": str(e)}

@FunctionTool
def create_log_based_metric(metric_name: str, description: str, log_name: str, match_text: str) -> dict:
    """
    Creates a log-based metric with correct escaping for 'gcloud logging metrics create'.
    """
    try:
        # Get current project
        project_id = subprocess.check_output("gcloud config get-value project", shell=True).decode().strip()

        # Compose raw filter expression
        raw_filter = f'logName="projects/{project_id}/logs/{log_name}" AND textPayload:"{match_text}"'

        # Use a list for subprocess to avoid all quoting issues
        cmd = [
            "gcloud", "logging", "metrics", "create", metric_name,
            f"--description={description}",
            f"--log-filter={raw_filter}"
        ]

        result = subprocess.run(
            cmd, 
            shell=True,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return {"message": "✅ Metric created successfully.", "stdout": result.stdout}
        else:
            return {
                "error": "❌ Failed to create metric.",
                "stderr": result.stderr,
                "full_command": " ".join(cmd)
            }

    except Exception as e:
        return {"error": str(e)}



@FunctionTool
def describe_log_based_metric(metric_name: str) -> dict:
    """
    Describes a previously created log-based metric.
    """
    try:
        result = subprocess.run(
            f"gcloud logging metrics describe {metric_name}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return {"message": "✅ Metric described successfully.", "stdout": result.stdout}
        else:
            return {"error": "❌ Failed to describe metric.", "stderr": result.stderr}
    except Exception as e:
        return {"error": str(e)}
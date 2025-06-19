import re
import shlex
import subprocess
from google.adk.tools.function_tool import FunctionTool


import subprocess
from google.adk.tools.function_tool import FunctionTool

# --- Core Functionality ---

@FunctionTool
def read_log_entries(log_filter: str, flags: str = "") -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud logging read \"{log_filter}\" {flags}",
            shell=True,
            text=True
        )
        return {"entries": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def write_custom_log_entry(log_name: str, message: str, flags: str = "") -> dict:
    try:
        subprocess.run(
            f"gcloud logging write {log_name} \"{message}\" {flags}",
            shell=True,
            check=True
        )
        return {"message": f"📝 Log written to '{log_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def copy_log_entries(source: str, destination: str, flags: str = "") -> dict:
    try:
        subprocess.run(
            f"gcloud logging copy {source} {destination} {flags}",
            shell=True,
            check=True
        )
        return {"message": f"📤 Logs copied from '{source}' to '{destination}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# --- Managing Logs ---

@FunctionTool
def list_logs() -> dict:
    try:
        output = subprocess.check_output("gcloud logging logs list", shell=True, text=True)
        return {"logs": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def delete_log(log_id: str) -> dict:
    try:
        subprocess.run(
            f"gcloud logging logs delete {log_id} --quiet",
            shell=True,
            check=True
        )
        return {"message": f"🗑️ Log '{log_id}' deleted."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# --- Managing Metrics ---

@FunctionTool
# def create_log_based_metric(metric_name: str, flags: str = "") -> dict:
#     try:
#         subprocess.run(
#             f"gcloud logging metrics create {metric_name} {flags}",
#             shell=True,
#             check=True
#         )
#         return {"message": f"📊 Metric '{metric_name}' created."}
#     except subprocess.CalledProcessError as e:
#         return {"error": str(e)}
def create_log_based_metric(metric_name: str, log_filter: str, description: str = "") -> dict:
    """
    Creates a log-based metric with proper validation and secure shell handling.
    """
    try:
        # Check gcloud availability
        if subprocess.call("which gcloud", shell=True) != 0:
            return {"error": "❌ 'gcloud' CLI is not installed or not in PATH."}

        # Validate metric name
        if not re.match(r'^[a-zA-Z0-9_-]+$', metric_name):
            return {"error": "❌ Invalid metric name. Use only letters, digits, underscores or hyphens."}

        # Validate filter fields
        if not any(f in log_filter for f in ["textPayload", "jsonPayload", "protoPayload"]):
            return {"error": "❌ Invalid filter. Must use 'textPayload', 'jsonPayload', or 'protoPayload'."}

        # Securely quote shell parameters
        quoted_filter = shlex.quote(log_filter)
        quoted_desc = shlex.quote(description) if description else ""

        # Build command
        cmd = (
            f"gcloud logging metrics create {metric_name} "
            f"--log-filter={quoted_filter} "
        )
        if description:
            cmd += f"--description={quoted_desc}"

        # Run command
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
        return {"message": f"📊 Metric '{metric_name}' created successfully.", "details": output}

    except subprocess.CalledProcessError as e:
        return {"error": f"🚨 Failed to create metric.\n{e.output if hasattr(e, 'output') else str(e)}"}


@FunctionTool
def describe_log_metric(metric_name: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud logging metrics describe {metric_name}",
            shell=True,
            text=True
        )
        return {"metric": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def list_log_metrics() -> dict:
    try:
        output = subprocess.check_output("gcloud logging metrics list", shell=True, text=True)
        return {"metrics": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def update_log_metric(metric_name: str, flags: str = "") -> dict:
    try:
        subprocess.run(
            f"gcloud logging metrics update {metric_name} {flags}",
            shell=True,
            check=True
        )
        return {"message": f"🔧 Metric '{metric_name}' updated."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def delete_log_metric(metric_name: str) -> dict:
    try:
        subprocess.run(
            f"gcloud logging metrics delete {metric_name} --quiet",
            shell=True,
            check=True
        )
        return {"message": f"🗑️ Metric '{metric_name}' deleted."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# | **Function**              | **Required Inputs**                           |
# | ------------------------- | --------------------------------------------- |
# | `read_log_entries`        | `log_filter`, *(optional)* `flags`            |
# | `write_custom_log_entry`  | `log_name`, `message`, *(optional)* `flags`   |
# | `copy_log_entries`        | `source`, `destination`, *(optional)* `flags` |
# | `list_logs`               | *(none)*                                      |
# | `delete_log`              | `log_id`                                      |
# | `create_log_based_metric` | `metric_name`, *(optional)* `flags`           |
# | `describe_log_metric`     | `metric_name`                                 |
# | `list_log_metrics`        | *(none)*                                      |
# | `update_log_metric`       | `metric_name`, *(optional)* `flags`           |
# | `delete_log_metric`       | `metric_name`                                 |

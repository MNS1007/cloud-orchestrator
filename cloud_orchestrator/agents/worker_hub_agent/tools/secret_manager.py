import json, os, subprocess, tempfile
from typing import Dict, List
from google.adk.tools import FunctionTool


def _gcloud(cmd: List[str]) -> str:
    """Helper function to execute gcloud commands."""
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)

@FunctionTool
def create_secret(
    project_id: str,
    secret_id: str,
    data: str,
    replication_policy: str = "automatic", # Can be 'automatic' or 'user-managed'
) -> Dict[str, str]:
    """
    Create a new secret in Google Cloud Secret Manager.
    The secret value is added as the initial version.
    """
    try:
       
        _gcloud([
            "gcloud", "secrets", "create", secret_id,
            f"--project={project_id}",
            f"--replication-policy={replication_policy}",
            "--format=value(name)"
        ])
        
        with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as tmp:
            tmp.write(data)
            tmp.flush() 
            version_name = _gcloud([
                "gcloud", "secrets", "versions", "add", secret_id,
                f"--project={project_id}",
                f"--data-file={tmp.name}",
                "--format=value(name)"
            ]).strip()
            os.remove(tmp.name) 

        return {"status": "success", "secret_name": secret_id, "version_name": version_name}
    except subprocess.CalledProcessError as e:
        
        return {"status": "error", "error_message": e.output.strip()}
    except Exception as e:
        
        return {"status": "error", "error_message": str(e)}


@FunctionTool
def add_version(
    project_id: str,
    secret_id: str,
    data: str,
) -> Dict[str, str]:
    """
    Add a new version to an existing secret in Google Cloud Secret Manager.
    """
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as tmp:
        tmp.write(data)
        tmp.flush() 
        try:
            
            version_name = _gcloud([
                "gcloud", "secrets", "versions", "add", secret_id,
                f"--project={project_id}",
                f"--data-file={tmp.name}",
                "--format=value(name)"
            ]).strip()
            return {"status": "success", "secret_name": secret_id, "version_name": version_name}
        except subprocess.CalledProcessError as e:
            
            return {"status": "error", "error_message": e.output.strip()}
        finally:
            os.remove(tmp.name)

def get_tools():
    
    return [create_secret, add_version]


import subprocess
from google.adk.tools.function_tool import FunctionTool

@FunctionTool
def create_vm(project_id: str, zone: str, instance_name: str, machine_type: str = "e2-micro", image_family: str = "debian-11", image_project: str = "debian-cloud") -> dict:
    """Create a new VM instance."""
    try:
        subprocess.run([
            "gcloud", "compute", "instances", "create", instance_name,
            f"--project={project_id}",
            f"--zone={zone}",
            f"--machine-type={machine_type}",
            f"--image-family={image_family}",
            f"--image-project={image_project}"
        ], check=True)

        return {
            "message": f"✅ VM '{instance_name}' created in project '{project_id}' (zone: {zone})."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to create VM. Details:\n{e}"
        }

@FunctionTool
def delete_vm(project_id: str, zone: str, instance_name: str) -> dict:
    """Delete an existing VM instance."""
    try:
        subprocess.run([
            "gcloud", "compute", "instances", "delete", instance_name,
            f"--project={project_id}",
            f"--zone={zone}",
            "--quiet"
        ], check=True)

        return {
            "message": f"✅ VM '{instance_name}' deleted from project '{project_id}' (zone: {zone})."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to delete VM. Details:\n{e}"
        }

@FunctionTool
def get_external_ip(project_id: str, zone: str, instance_name: str) -> dict:
    """Get the external IP address of a VM."""
    try:
        result = subprocess.run([
            "gcloud", "compute", "instances", "describe", instance_name,
            f"--project={project_id}",
            f"--zone={zone}",
            "--format=get(networkInterfaces[0].accessConfigs[0].natIP)"
        ], check=True, capture_output=True, text=True)

        ip = result.stdout.strip()
        return {
            "external_ip": ip
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to get external IP. Details:\n{e}"
        }

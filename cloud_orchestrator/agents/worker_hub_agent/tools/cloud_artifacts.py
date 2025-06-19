import subprocess
from google.adk.tools.function_tool import FunctionTool

# 1. Create an Artifact Registry repository
@FunctionTool
def create_artifact_repository(repo_name: str, format: str, location: str, description: str = "") -> dict:
    try:
        subprocess.run(
            f"gcloud artifacts repositories create {repo_name} "
            f"--repository-format={format} --location={location} "
            f"--description=\"{description}\"",
            shell=True,
            check=True
        )
        return {"message": f"📦 Repository '{repo_name}' created with format '{format}' in region '{location}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# 2. Describe a repository
@FunctionTool
def describe_artifact_repository(repo_name: str, location: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud artifacts repositories describe {repo_name} --location={location}",
            shell=True,
            text=True
        )
        return {"description": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# 3. List repositories
@FunctionTool
def list_artifact_repositories(location: str = "") -> dict:
    try:
        cmd = f"gcloud artifacts repositories list --location={location}" if location else "gcloud artifacts repositories list"
        output = subprocess.check_output(cmd, shell=True, text=True)
        return {"repositories": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# 4. Delete a repository
@FunctionTool
def delete_artifact_repository(repo_name: str, location: str) -> dict:
    try:
        subprocess.run(
            f"gcloud artifacts repositories delete {repo_name} --location={location} --quiet",
            shell=True,
            check=True
        )
        return {"message": f"🗑️ Repository '{repo_name}' deleted from region '{location}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# 5. Update a repository (e.g., description)
@FunctionTool
def update_artifact_repository(repo_name: str, location: str, flags: str) -> dict:
    try:
        subprocess.run(
            f"gcloud artifacts repositories update {repo_name} --location={location} {flags}",
            shell=True,
            check=True
        )
        return {"message": f"🛠️ Repository '{repo_name}' updated with: {flags}"}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# 6. List available Artifact Registry locations
@FunctionTool
def list_artifact_locations() -> dict:
    try:
        output = subprocess.check_output("gcloud artifacts locations list", shell=True, text=True)
        return {"locations": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

import subprocess
from google.adk.tools.function_tool import FunctionTool

# artifact registry api is required, here there is a tool that does that
# the docker file should exist on the local system and local path should be given

@FunctionTool
def enable_artifact_registry_api(project_id: str) -> dict:
    try:
        subprocess.run(
            f"gcloud services enable artifactregistry.googleapis.com --project={project_id}",
            shell=True, check=True
        )
        return {"message": "✅ Artifact Registry API enabled."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to enable Artifact Registry API: {e}"}


@FunctionTool
def create_docker_repository(project_id: str, location: str, repository_name: str) -> dict:
    try:
        result = subprocess.run(
            f"gcloud artifacts repositories create {repository_name} "
            f"--repository-format=docker "
            f"--location={location} "
            f"--project={project_id}",
            shell=True, check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("STDOUT of create docker repository:\n", result.stdout)
        print("STDERR:\n", result.stderr)
        return {"message": f"✅ Docker repository '{repository_name}' created in {location}."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to create repository: {e}"}
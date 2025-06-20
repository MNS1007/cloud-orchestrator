import os
import subprocess
from google.adk.tools.function_tool import FunctionTool

# cloud build api is required, here there is a tool that does that
# the docker file should exist on the local system and local path should be given
# and docker should be running

# Global variable to store the working directory
WORKING_DIRECTORY = None

@FunctionTool
def set_working_directory(path: str) -> dict:
    global WORKING_DIRECTORY
    abs_path = os.path.abspath(path)
    if not os.path.isdir(abs_path):
        return {"error": f"❌ Directory does not exist: {abs_path}"}
    WORKING_DIRECTORY = abs_path
    return {"message": f"✅ Working directory set to: {abs_path}"}

@FunctionTool
def enable_cloud_build_api(project_id: str) -> dict:
    try:
        subprocess.run(
            f"gcloud services enable cloudbuild.googleapis.com --project={project_id}",
            shell=True, check=True
        )
        return {"message": "✅ Cloud Build API enabled."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to enable Cloud Build API: {e}"}


@FunctionTool
def configure_docker_auth(region: str) -> dict:
    try:
        subprocess.run(
            f"gcloud auth configure-docker {region}-docker.pkg.dev",
            shell=True, check=True
        )
        return {"message": f"✅ Docker authentication configured for {region}."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to configure Docker auth: {e}"}


@FunctionTool
def build_and_push_docker_image(
    project_id: str,
    location: str,
    repository_name: str,
    image_name: str,
    local_dir_path: str , 
) -> dict:
    global WORKING_DIRECTORY
    image_uri = f"{location}-docker.pkg.dev/{project_id}/{repository_name}/{image_name}:latest"
    try:
        # Use the set working directory if available
        target_dir = WORKING_DIRECTORY if WORKING_DIRECTORY else os.path.abspath(local_dir_path)
        print("Current working directory before chdir:", os.getcwd())
        print("Attempting to change directory to:", target_dir)
        os.chdir(target_dir)
        subprocess.run(
            f"docker build -t {image_uri} .",
            shell=True, check=True
        )
        subprocess.run(
            f"docker push {image_uri}",
            shell=True, check=True
        )
        return {"message": f"✅ Docker image pushed: {image_uri}"}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to build or push image: {e}"}
    except FileNotFoundError as fnf:
        return {"error": f"❌ Directory not found: {fnf}", "current_working_directory": os.getcwd()}
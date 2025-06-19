import os
import subprocess
from google.adk.tools.function_tool import FunctionTool

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
    local_dir_path: str = "./my-docker-app"
) -> dict:
    image_uri = f"{location}-docker.pkg.dev/{project_id}/{repository_name}/{image_name}:latest"
    try:
        os.chdir(local_dir_path)
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

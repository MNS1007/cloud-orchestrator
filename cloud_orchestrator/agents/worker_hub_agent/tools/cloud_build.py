import subprocess
from google.adk.tools.function_tool import FunctionTool

# --- Core Cloud Build Operations ---

@FunctionTool
def submit_cloud_build(source_dir: str = ".", config_file: str = "cloudbuild.yaml", extra_flags: str = "") -> dict:
    """
    Submits a build using a local directory and cloudbuild.yaml config.
    """
    try:
        subprocess.run(
            f"gcloud builds submit {source_dir} --config={config_file} {extra_flags}",
            shell=True,
            check=True
        )
        return {"message": f"🚀 Build submitted from '{source_dir}' using '{config_file}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def list_cloud_builds(flags: str = "") -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud builds list {flags}",
            shell=True,
            text=True
        )
        return {"builds": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def describe_cloud_build(build_id: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud builds describe {build_id}",
            shell=True,
            text=True
        )
        return {"description": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def cancel_cloud_build(build_id: str) -> dict:
    try:
        subprocess.run(
            f"gcloud builds cancel {build_id}",
            shell=True,
            check=True
        )
        return {"message": f"⛔ Build '{build_id}' has been canceled."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def stream_cloud_build_logs(build_id: str) -> dict:
    try:
        subprocess.run(
            f"gcloud builds log {build_id}",
            shell=True,
            check=True
        )
        return {"message": f"📡 Streaming logs for build '{build_id}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def get_default_build_service_account() -> dict:
    try:
        output = subprocess.check_output(
            "gcloud builds get-default-service-account",
            shell=True,
            text=True
        )
        return {"service_account": output.strip()}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# Additional functions to support gcloud build

# 1. Enable Cloud Build and Artifact Registry APIs
@FunctionTool
def enable_required_apis() -> dict:
    try:
        subprocess.run(
            "gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com",
            shell=True,
            check=True
        )
        return {"message": "✅ Required APIs enabled: Cloud Build & Artifact Registry."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# 3. Configure Docker to Authenticate with Artifact Registry
@FunctionTool
def configure_docker_auth(region: str = "us-central1") -> dict:
    try:
        subprocess.run(
            f"gcloud auth configure-docker {region}-docker.pkg.dev",
            shell=True,
            check=True
        )
        return {"message": f"🔐 Docker authentication configured for {region}-docker.pkg.dev"}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# 4. Build Docker Image Locally
@FunctionTool
def docker_build_image(tag: str, directory: str = ".") -> dict:
    try:
        subprocess.run(
            f"docker build -t {tag} {directory}",
            shell=True,
            check=True
        )
        return {"message": f"🛠️ Docker image built with tag '{tag}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

# 5. Push Docker Image to Artifact Registry
@FunctionTool
def docker_push_image(tag: str) -> dict:
    try:
        subprocess.run(
            f"docker push {tag}",
            shell=True,
            check=True
        )
        return {"message": f"📤 Docker image '{tag}' pushed to Artifact Registry."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

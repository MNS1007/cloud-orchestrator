import subprocess
from typing import Optional, Dict
from google.adk.tools import FunctionTool


@FunctionTool
def create_service(
    service_type: str,
    service_name: str,
    source_or_image: str,
    region: str,
    runtime: Optional[str] = None,
    entry_point: Optional[str] = None,
    project_id: Optional[str] = None
) -> dict:
    api_map = {
        "docker": ["run.googleapis.com"],
        "git": ["run.googleapis.com", "cloudbuild.googleapis.com"],
        "function": ["cloudfunctions.googleapis.com"]
    }

    if service_type not in api_map:
        return {"status": "error", "message": f"❌ Invalid service_type '{service_type}'."}
    if service_type == "function" and not runtime:
        return {"status": "error", "message": "❌ 'runtime' is required for Cloud Functions."}

    for api in api_map[service_type]:
        enable_cmd = f"gcloud services enable {api}"
        if project_id:
            enable_cmd += f" --project {project_id}"
        try:
            subprocess.run(enable_cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ Enabled API: {api}")
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"❌ Failed enabling API {api}", "details": e.stderr.strip() or str(e)}

    if service_type == "docker":
        cmd = (
            f"gcloud run deploy {service_name} "
            f"--image={source_or_image} "
            f"--region={region} --platform=managed --quiet"
        )
        if project_id:
            cmd += f" --project {project_id}"
        description = "Cloud Run deployment (Docker)"

    elif service_type == "git":
        image_tag = f"gcr.io/{project_id}/{service_name}"
        build_cmd = (
            f"gcloud builds submit {source_or_image} "
            f"--tag={image_tag} --quiet"
        )
        if project_id:
            build_cmd += f" --project {project_id}"

        try:
            subprocess.run(build_cmd, shell=True, check=True, capture_output=True, text=True)
            print("✅ Cloud Build succeeded")
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": "❌ Cloud Build failed.", "details": e.stderr.strip() or str(e)}

        cmd = (
            f"gcloud run deploy {service_name} "
            f"--image={image_tag} "
            f"--region={region} --platform=managed --quiet"
        )
        if project_id:
            cmd += f" --project={project_id}"
        description = "Cloud Run deployment (Git source)"

    elif service_type == "function":
        cmd = (
            f"gcloud functions deploy {service_name} "
            f"--runtime={runtime} "
            f"--trigger-http "
            f"--region={region} --quiet"
        )
        if entry_point:
            cmd += f" --entry-point={entry_point}"
        if source_or_image:
            cmd += f" --source={source_or_image}"
        if project_id:
            cmd += f" --project={project_id}"
        description = "Cloud Function deployment"

    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} succeeded")
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Failed during {description}", "details": e.stderr.strip() or str(e)}

    return {
        "status": "success",
        "message": f"✅ {description} completed for '{service_name}'.",
        "details": result.stdout.strip()
    }


@FunctionTool
def update_env(
    service_type: str,
    service_name: str,
    region: str,
    env_vars: Dict[str, str],
    project_id: Optional[str] = None,
    source_dir: Optional[str] = None
) -> dict:
    api_map = {
        "docker": ["run.googleapis.com"],
        "git": ["run.googleapis.com"],
        "function": ["cloudfunctions.googleapis.com"]
    }

    if service_type not in api_map:
        return {"status": "error", "message": f"❌ Invalid service_type '{service_type}'."}
    if not env_vars:
        return {"status": "error", "message": "❌ No environment variables provided to update."}

    for api in api_map[service_type]:
        enable_cmd = f"gcloud services enable {api}"
        if project_id:
            enable_cmd += f" --project {project_id}"
        try:
            subprocess.run(enable_cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"✅ Enabled API: {api}")
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"❌ Failed enabling API {api}", "details": e.stderr.strip() or str(e)}

    env_str = ",".join([f"{k}={v}" for k, v in env_vars.items()])

    if service_type in ["docker", "git"]:
        cmd = (
            f"gcloud run services update {service_name} "
            f"--update-env-vars={env_str} "
            f"--region={region} --platform=managed --quiet"
        )
        if project_id:
            cmd += f" --project={project_id}"
        description = "Cloud Run env var update"

    elif service_type == "function":
        if not source_dir:
            return {"status": "error", "message": "❌ 'source_dir' is required for Cloud Functions env update."}
        cmd = (
            f"gcloud functions deploy {service_name} "
            f"--region={region} "
            f"--source={source_dir} "
            f"--update-env-vars={env_str} --quiet"
        )
        if project_id:
            cmd += f" --project={project_id}"
        description = "Cloud Function env var update"

    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} succeeded")
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Failed during {description}", "details": e.stderr.strip() or str(e)}

    return {
        "status": "success",
        "message": f"✅ {description} completed for '{service_name}'.",
        "details": result.stdout.strip()
    }


@FunctionTool
def pause_service(
    service_name: str,
    region: str,
    project_id: str
) -> dict:
    try:
        revision_cmd = (
            f"gcloud run services describe {service_name} "
            f"--region={region} --project={project_id} "
            f"--format=value(status.latestReadyRevisionName)"
        )
        get_revision = subprocess.run(revision_cmd, shell=True, capture_output=True, text=True, check=True)
        latest_revision = get_revision.stdout.strip()

        if not latest_revision:
            return {"status": "error", "message": f"❌ Could not retrieve latest revision for '{service_name}'."}

        print(f"✅ Retrieved latest revision: {latest_revision}")

        pause_cmd = (
            f"gcloud run services update-traffic {service_name} "
            f"--to-revisions={latest_revision}=0 "
            f"--region={region} --project={project_id} --quiet"
        )

        subprocess.run(pause_cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ Service paused (0% traffic)")

        return {
            "status": "success",
            "message": f"✅ Successfully paused service '{service_name}'.",
            "details": f"Revision {latest_revision} set to 0% traffic."
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"❌ Failed to pause service '{service_name}'.",
            "details": e.stderr.strip() if e.stderr else str(e)
        }


@FunctionTool
def delete_service(
    service_name: str,
    region: str,
    project_id: str
) -> dict:
    try:
        delete_cmd = (
            f"gcloud run services delete {service_name} "
            f"--region={region} --platform=managed --project={project_id} --quiet"
        )

        result = subprocess.run(delete_cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ Service deleted")

        return {
            "status": "success",
            "message": f"✅ Successfully deleted service '{service_name}'.",
            "details": result.stdout.strip()
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"❌ Failed to delete service '{service_name}'.",
            "details": e.stderr.strip() if e.stderr else str(e)
        }


def get_tools():
    return [create_service, update_env, pause_service, delete_service]

"""
Prereqs : 

The service‑account running the agent must have:
  • roles/container.admin   – cluster mgmt
  • roles/container.clusterAdmin (or viewer) – get‑credentials
  • IAM roles to create the underlying GCP resources

Helm and kubectl CLIs must be on the PATH inside the agent container.
"""
from __future__ import annotations

import subprocess, tempfile, os
from typing import Dict, List
from google.adk.tools import FunctionTool
from time import time


def _sh(cmd: List[str]) -> str:
    """Run a shell command and capture stdout; raise with stderr on failure."""
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.output.strip()) from exc


def _get_credentials(project_id: str, cluster_name: str, region: str):
   
    _sh([
        "gcloud", "container", "clusters", "get-credentials", cluster_name,
        f"--region={region}", f"--project={project_id}"
    ])


@FunctionTool
def create_cluster(
    project_id: str,
    cluster_name: str,
    region: str = "us-central1",
    release_channel: str = "regular", 
) -> Dict[str, str]:
    """Create a new GKE **Autopilot** cluster.

    Returns
    -------
    dict
        status : "success" | "error"
        cluster_resource : resource name on success
        error_message    : string on error
    """
    try:
        resource = _sh([
            "gcloud", "container", "clusters", "create-auto", cluster_name,
            f"--region={region}", f"--release-channel={release_channel}",
            f"--project={project_id}", "--format=value(name)"
        ]).strip()
        return {"status": "success", "cluster_resource": resource}
    except RuntimeError as e:
        return {"status": "error", "error_message": str(e)}


@FunctionTool
def helm_install(
    project_id: str,
    cluster_name: str,
    chart_name: str,
    namespace: str,
    values_yaml: str | None = None,   
    region: str = "us-central1",
) -> Dict[str, str]:
    """Install or upgrade a Helm chart on the specified cluster."""
    try:
        _get_credentials(project_id, cluster_name, region)

        values_arg: List[str] = []
        if values_yaml:
            with tempfile.NamedTemporaryFile("w+", suffix=".yaml", delete=False) as tmp:
                tmp.write(values_yaml)
                tmp.flush()
                values_file = tmp.name
            values_arg = ["-f", values_file]
        else:
            values_file = None

        _sh([
            "helm", "upgrade", "--install", chart_name, chart_name,
            "--namespace", namespace, "--create-namespace", *values_arg
        ])
        if values_file:
            os.remove(values_file)
        return {"status": "success", "message": f"{chart_name} deployed"}
    except RuntimeError as e:
        return {"status": "error", "error_message": str(e)}


@FunctionTool
def scale_deployment(
    project_id: str,
    cluster_name: str,
    deployment_name: str,
    replicas: int,
    namespace: str = "default",
    region: str = "us-central1",
) -> Dict[str, str]:
    """Scale an existing Deployment to the desired replica count."""
    try:
        _get_credentials(project_id, cluster_name, region)
        _sh([
            "kubectl", "scale", "deployment", deployment_name,
            f"--replicas={replicas}", "-n", namespace
        ])
        return {"status": "success", "replicas": str(replicas)}
    except RuntimeError as e:
        return {"status": "error", "error_message": str(e)}

@FunctionTool
def delete_cluster(
    project_id: str,
    cluster_name: str,
    region: str = "us-central1",
    wait_seconds: int = 600,
) -> Dict[str, str]:
    """Delete an Autopilot cluster and wait for completion."""
    try:
        _sh([
            "gcloud", "container", "clusters", "delete", cluster_name,
            f"--region={region}", f"--project={project_id}", "--quiet"
        ])
    
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            try:
                _sh([
                    "gcloud", "container", "clusters", "describe", cluster_name,
                    f"--region={region}", f"--project={project_id}", "--format=value(name)"
                ])
                time.sleep(10)
            except RuntimeError:
                return {"status": "success", "message": "cluster deleted"}
        return {"status": "error", "error_message": "timeout waiting for delete"}
    except RuntimeError as e:
        return {"status": "error", "error_message": str(e)}


def get_tools():
    
    return [create_cluster, helm_install, scale_deployment]

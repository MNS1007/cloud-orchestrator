"""
Vertex AI FunctionTools (SDK-based)
----------------------------------
Implements four tools using google-cloud-aiplatform:
1. train_custom – launch a CustomTrainingJob (async)
2. deploy_endpoint – upload model & deploy to endpoint
3. batch_predict – Model.batch_predict (async)
4. delete_endpoint – undeploy + delete endpoint

Requires:
  pip install --upgrade google-cloud-aiplatform
  gcloud auth application-default login  # or ADC key
  Service‑account needs roles/aiplatform.user
"""
from __future__ import annotations
import time
from typing import Dict, Optional
from google.adk.tools import FunctionTool
from google.cloud import aiplatform


def _init(project_id: str, region: str):
    """Initialize Vertex SDK once per call."""
    aiplatform.init(project=project_id, location=region)

@FunctionTool
def train_custom(
    project_id: str,
    job_name: str,
    python_package_uri: str,
    python_module: str,
    staging_bucket: str,
    region: str = "us-central1",
    machine_type: str = "n1-standard-4",
) -> Dict[str, str]:
    try:
        _init(project_id, region)
        job = aiplatform.CustomTrainingJob(
            display_name=job_name,
            python_package_uri=python_package_uri,
            python_module_name=python_module,
            staging_bucket=staging_bucket,
        )
        job.run(replica_count=1, machine_type=machine_type, sync=False)
        return {"status": "success", "job_name": job.resource_name}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@FunctionTool
def deploy_endpoint(
    project_id: str,
    model_display_name: str,
    artifact_uri: str,
    endpoint_display_name: str,
    region: str = "us-central1",
    machine_type: str = "n1-standard-4",
) -> Dict[str, str]:
    """Upload artifact and deploy model to new endpoint."""
    try:
        _init(project_id, region)
        model = aiplatform.Model.upload(
            display_name=model_display_name,
            artifact_uri=artifact_uri,
            serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
            sync=True,
        )
        endpoint = model.deploy(
            deployed_model_display_name=endpoint_display_name,
            machine_type=machine_type,
            traffic_split={"0": 100},
            sync=True,
        )
        return {
            "status": "success",
            "endpoint": endpoint.resource_name,
            "model": model.resource_name,
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

@FunctionTool
def batch_predict(
    project_id: str,
    model_id: str,
    input_uri: str,
    output_uri: str,
    region: str = "us-central1",
    job_name: Optional[str] = None,
) -> Dict[str, str]:
    try:
        _init(project_id, region)
        model = aiplatform.Model(model_id)
        if not job_name:
            job_name = f"batch-{int(time.time())}"
        job = model.batch_predict(
            job_display_name=job_name,
            gcs_source=[input_uri],
            gcs_destination_prefix=output_uri,
            instances_format="jsonl",
            predictions_format="jsonl",
            sync=False,
        )
        job.wait_for_resource_creation()
        return {"status": "success", "batch_job": job.resource_name}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

@FunctionTool
def delete_endpoint(
    project_id: str,
    endpoint_id: str,
    region: str = "us-central1",
) -> Dict[str, str]:
    try:
        _init(project_id, region)
        endpoint = aiplatform.Endpoint(endpoint_id)
        endpoint.undeploy_all()
        endpoint.delete()
        return {"status": "success", "message": "endpoint deleted"}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def get_tools():
    return [train_custom, deploy_endpoint, batch_predict, delete_endpoint]

import subprocess
from google.adk.tools import FunctionTool
from typing import Optional


@FunctionTool
def create_cluster(
    cluster_name: str,
    region: str,
    num_workers: int,
    project_id: str
) -> dict:
    """
    Creates a Google Cloud Dataproc cluster with predefined configuration.

    Args:
        cluster_name (str): Name of the Dataproc cluster.
        region (str): GCP region where the cluster will be deployed.
        num_workers (int): Number of worker nodes.
        project_id (str): GCP project ID.

    Returns:
        dict: Result with status, message, and details.
    """
    try:
        #  Step 1: Enable the Dataproc API
        enable_api_cmd = (
            f"gcloud services enable dataproc.googleapis.com "
            f"--project {project_id}"
        )
        subprocess.run(
            enable_api_cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Enabled Dataproc API")

        # Step 2: Create the Dataproc cluster with fixed settings
        create_cluster_cmd = (
            f"gcloud dataproc clusters create {cluster_name} "
            f"--region={region} "
            f"--num-workers={num_workers} "
            f"--master-boot-disk-size=50GB "
            f"--worker-boot-disk-size=50GB "
            f"--max-idle=30m "
            f"--enable-component-gateway "
            f"--image-version=2.1-debian11 "
            f"--project={project_id} "
            f"--quiet"
        )
        completed_process = subprocess.run(
            create_cluster_cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Cluster creation completed")

        return {
            "status": "success",
            "message": f"✅ Dataproc cluster '{cluster_name}' successfully created in region '{region}'.",
            "details": completed_process.stdout.strip()
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "❌ Failed to create Dataproc cluster.",
            "details": e.stderr.strip() if e.stderr else str(e)
        }


@FunctionTool
def run_pyspark(
    bucket_name: str,
    pyspark_filename: str,
    cluster_name: str,
    region: str,
    project_id: str,
    input_filename: Optional[str] = None,
    output_foldername: Optional[str] = None
) -> dict:
    """
    Runs a PySpark job on a Google Cloud Dataproc cluster.

    Args:
        bucket_name (str): Name of the GCS bucket (without gs://).
        pyspark_filename (str): Name of the PySpark script file in the bucket (e.g., wordcount.py).
        cluster_name (str): Name of the Dataproc cluster.
        region (str): GCP region where the cluster is deployed.
        project_id (str): GCP project ID.
        input_filename (str, optional): Name of the input file in the bucket.
        output_foldername (str, optional): Name of the output folder location in the bucket.

    Returns:
        dict: Result with status, message, and details.
    """
    try:
        if not bucket_name or not pyspark_filename or not project_id:
            return {
                "status": "error",
                "message": "❌ 'bucket_name', 'pyspark_filename', and 'project_id' are required.",
                "details": ""
            }

        # Construct full GCS paths
        pyspark_file = f"gs://{bucket_name}/{pyspark_filename}"
        input_path = f"gs://{bucket_name}/{input_filename}" if input_filename else None
        output_path = f"gs://{bucket_name}/{output_foldername}" if output_foldername else None

        # Base command
        cmd = (
            f"gcloud dataproc jobs submit pyspark {pyspark_file} "
            f"--cluster={cluster_name} "
            f"--project={project_id} "
            f"--region={region} "
            f"--quiet"
        )

        # Append positional args if provided
        positional_args = []
        if input_path:
            positional_args.append(input_path)
        if output_path:
            positional_args.append(output_path)

        if positional_args:
            cmd += " -- " + " ".join(positional_args)
        else:
            print("⚠️ Warning: No input/output files specified. Ensure your script handles arguments correctly.")

        # Execute the command
        completed_process = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )

        print("✅ PySpark job submitted successfully")

        return {
            "status": "success",
            "message": f"✅ PySpark job '{pyspark_filename}' submitted to cluster '{cluster_name}' in region '{region}'.",
            "details": completed_process.stdout.strip()
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "❌ Failed to submit PySpark job.",
            "details": e.stderr.strip() if e.stderr else str(e)
        }

@FunctionTool
def delete_cluster(
    cluster_name: str,
    region: str,
    project_id: str
) -> dict:
    """
    Deletes a Google Cloud Dataproc cluster.

    Args:
        cluster_name (str): Name of the Dataproc cluster to delete.
        region (str): GCP region where the cluster is deployed.
        project_id (str): GCP project ID.

    Returns:
        dict: Result with status, message, and details.
    """
    try:
        # Step 1: Delete the Dataproc cluster
        delete_cluster_cmd = (
            f"gcloud dataproc clusters delete {cluster_name} "
            f"--region={region} "
            f"--project={project_id} "
            f"--quiet"
        )
        completed_process = subprocess.run(
            delete_cluster_cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Cluster deletion completed")

        return {
            "status": "success",
            "message": f"🗑️ Dataproc cluster '{cluster_name}' successfully deleted from region '{region}'.",
            "details": completed_process.stdout.strip()
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "❌ Failed to delete Dataproc cluster.",
            "details": e.stderr.strip() if e.stderr else str(e)
        }



def get_tools():
    return [create_cluster, run_pyspark, delete_cluster]

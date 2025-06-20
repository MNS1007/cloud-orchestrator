# bigquery.py
import subprocess
import json
from google.adk.tools.function_tool import FunctionTool

@FunctionTool
def create_dataset(project_id: str, dataset_id: str, location: str = "US") -> dict:
    """
    Creates a BigQuery dataset in the specified location.
    """
    try:
        subprocess.run([
            "gcloud", "services", "enable", "bigquery.googleapis.com", "--project", project_id
        ], check=True)

        subprocess.run([
            "bq", "--project_id", project_id, "mk", 
            f"--dataset", 
            f"--location={location}", 
            f"{project_id}:{dataset_id}"
        ], check=True)

        return {
            "message": f"✅ Dataset '{dataset_id}' created in location '{location}' under project '{project_id}'."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to create dataset. Details:\n{e}"
        }

@FunctionTool
def create_table(project_id: str, dataset_id: str, table_id: str, schema: str) -> dict:
    """
    Creates a BigQuery table using a schema string like:
    'customer_id:STRING,age:INTEGER,signup_date:TIMESTAMP'
    """
    try:
        subprocess.run([
            "gcloud", "services", "enable", "bigquery.googleapis.com", "--project", project_id
        ], check=True)

        subprocess.run([
            "bq", "--project_id", project_id, "mk",
            f"--table", f"{dataset_id}.{table_id}",
            schema
        ], check=True)

        return {
            "message": f"✅ Table '{dataset_id}.{table_id}' created in project '{project_id}'."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to create table. Details:\n{e}"
        }

@FunctionTool
def insert_json(project_id: str, dataset_id: str, table_id: str, rows: list) -> dict:
    """
    Inserts JSON rows into the specified BigQuery table.
    
    Parameters:
    - rows: A list of dictionaries representing rows to insert.
    """
    try:
        subprocess.run([
            "gcloud", "services", "enable", "bigquery.googleapis.com", "--project", project_id
        ], check=True)

        # Save JSON to a temporary file
        temp_file = "/tmp/bq_insert.json"
        with open(temp_file, "w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

        subprocess.run([
            "bq", "--project_id", project_id, "insert",
            f"{dataset_id}.{table_id}", temp_file
        ], check=True)

        return {
            "message": f"✅ Inserted {len(rows)} rows into '{dataset_id}.{table_id}'."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to insert rows. Details:\n{e}"
        }

@FunctionTool
def export_table_gcs(project_id: str, dataset_id: str, table_id: str, gcs_uri: str, export_format: str = "CSV") -> dict:
    """
    Exports a BigQuery table to Google Cloud Storage in the specified format.
    
    Parameters:
    - project_id: GCP project ID
    - dataset_id: BigQuery dataset ID
    - table_id: BigQuery table ID
    - gcs_uri: Destination GCS URI (e.g., gs://my-bucket/exports/myfile.csv)
    - export_format: One of 'CSV', 'JSON', or 'AVRO'
    """
    try:
        subprocess.run([
            "gcloud", "services", "enable", "bigquery.googleapis.com", "--project", project_id
        ], check=True)

        subprocess.run([
            "bq", "--project_id", project_id, "extract",
            f"--destination_format={export_format.upper()}",
            f"{dataset_id}.{table_id}",
            gcs_uri
        ], check=True)

        return {
            "message": f"📤 Table '{dataset_id}.{table_id}' exported to '{gcs_uri}' in {export_format.upper()} format."
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to export table. Details:\n{e}"
        }
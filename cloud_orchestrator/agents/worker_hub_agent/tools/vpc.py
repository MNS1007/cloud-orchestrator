from google.adk.tools import FunctionTool
import subprocess
import requests
from datetime import datetime, timedelta
import zoneinfo
from typing import Optional, List

NY_TZ = zoneinfo.ZoneInfo("America/New_York")


@FunctionTool
def create_firestore_db(
    project_id: str,
    location_id: str,
    db_name: str,
    collection_name: str,
    document_data: Optional[list] = None,
    add_documents: bool = False,
    timestamp: Optional[str] = None  # Options: "createdAt", "expiresAt"
) -> dict:
    """
    Creates Firestore database (native mode) and optionally adds documents.
    """
    messages = []
    inserted_docs = []
    firestore_type = "firestore-native"

    if document_data is None:
        document_data = []

    try:
        subprocess.run(f"gcloud services enable firestore.googleapis.com --project={project_id}", shell=True, check=True)
        messages.append("✅ Firestore API enabled.")
        subprocess.run(f"gcloud config set project {project_id}", shell=True, check=True)
        messages.append("✅ GCP project set.")

        check_cmd = f"gcloud firestore databases describe --database={db_name}"
        check_proc = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

        db_exists = check_proc.returncode == 0

        if not db_exists:
            create_cmd = (
                f"gcloud firestore databases create --database={db_name} "
                f"--location={location_id} --type={firestore_type}"
            )
            subprocess.run(create_cmd, shell=True, check=True)
            messages.append(f"✅ Firestore DB '{db_name}' created in {location_id}.")
        else:
            messages.append(f"✅ Firestore DB '{db_name}' already exists.")

        if add_documents and collection_name and document_data:
            data_result = _add_documents(
                project_id=project_id,
                db_name=db_name,
                collection_name=collection_name,
                document_data=document_data,
                timestamp=timestamp
            )
            messages.append(data_result["message"])
            inserted_docs.extend(data_result.get("inserted_documents", []))
        else:
            messages.append("ℹ️ Skipping data insertion. Set `add_documents=True` to insert.")

        return {"status": "success", "message": "\n".join(messages), "inserted_documents": inserted_docs}

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Command failed: {e.stderr or str(e)}"}
    except Exception as ex:
        return {"status": "error", "message": f"❌ Unexpected error: {str(ex)}"}


def _add_documents(
    project_id: str,
    db_name: str,
    collection_name: str,
    document_data: List[dict],
    timestamp: Optional[str] = None  # "createdAt" | "expiresAt"
) -> dict:
    inserted_docs = []
    messages = []

    expires_days = 15  # fixed TTL duration for 'expiresAt'

    try:
        token_proc = subprocess.run(
            "gcloud auth print-access-token", shell=True, check=True, capture_output=True
        )
        token = token_proc.stdout.decode("utf-8").strip()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        for idx, doc in enumerate(document_data):
            document_id = doc.get("id")
            if not document_id:
                messages.append(f"❌ Missing 'id' in document at index {idx}. Skipping.")
                continue

            field_list = [k for k in doc.keys() if k != "id"]

            if timestamp in ("createdAt", "expiresAt"):
                now_ny = datetime.now(tz=NY_TZ)
                if timestamp == "createdAt":
                    doc["createdAt"] = now_ny.isoformat()
                elif timestamp == "expiresAt":
                    expire_at = now_ny + timedelta(days=expires_days)
                    doc["expiresAt"] = expire_at.isoformat()
                field_list.append(timestamp)

            fields = {}
            for field in field_list:
                value = doc.get(field)
                if value is None:
                    continue
                if isinstance(value, bool):
                    fields[field] = {"booleanValue": value}
                elif isinstance(value, int):
                    fields[field] = {"integerValue": str(value)}
                elif isinstance(value, float):
                    fields[field] = {"doubleValue": value}
                elif isinstance(value, str) and value.endswith("Z") and "T" in value:
                    fields[field] = {"timestampValue": value}
                else:
                    fields[field] = {"stringValue": str(value)}

            data = {"fields": fields}
            url = (
                f"https://firestore.googleapis.com/v1/projects/{project_id}/"
                f"databases/{db_name}/documents/{collection_name}/{document_id}"
            )

            response = requests.patch(url, headers=headers, json=data)
            if response.status_code in (200, 201):
                doc_name = response.json().get("name", "unknown").split("/")[-1]
                inserted_docs.append(doc_name)
                messages.append(f"✅ Document '{doc_name}' inserted/updated.")
            else:
                messages.append(f"❌ Error adding document {idx + 1}: {response.text}")

    except subprocess.CalledProcessError as e:
        messages.append(f"❌ Auth error: {e.stderr.decode() if e.stderr else str(e)}")
    except Exception as ex:
        messages.append(f"❌ Unexpected error: {str(ex)}")

    return {
        "status": "complete",
        "inserted_documents": inserted_docs,
        "message": "\n".join(messages)
    }


@FunctionTool
def set_ttl(
    project_id: str,
    db_name: str,
    collection_name: str,
    ttl_field: str = "expiresAt"
) -> dict:
    """
    Sets TTL policy on a Firestore collection using the specified TTL field.
    """
    messages = []

    try:
        token_proc = subprocess.run(
            "gcloud auth print-access-token", shell=True, check=True, capture_output=True
        )
        token = token_proc.stdout.decode("utf-8").strip()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = (
            f"https://firestore.googleapis.com/v1/projects/{project_id}/"
            f"databases/{db_name}/collectionGroups/{collection_name}/ttlConfig"
        )
        data = {
            "ttlPolicy": {
                "field": ttl_field
            }
        }

        response = requests.patch(url, headers=headers, json=data)
        if response.status_code in (200, 201):
            messages.append(f"✅ TTL policy set on '{collection_name}' using field '{ttl_field}'.")
            return {"status": "success", "message": "\n".join(messages)}
        else:
            messages.append(f"❌ Failed to set TTL: {response.text}")
            return {"status": "error", "message": "\n".join(messages)}

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Command error: {e.stderr or str(e)}"}
    except Exception as ex:
        return {"status": "error", "message": f"❌ Unexpected error: {str(ex)}"}


def get_tools():
    return [create_firestore_db, set_ttl]

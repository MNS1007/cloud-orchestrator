from google.adk.tools import FunctionTool
import subprocess
import requests
import uuid
from typing import Optional, List

@FunctionTool
def create_firestore_db(
    project_id: str,
    location_id: str,
    db_name: str,
    collection_name: Optional[str] = None,
    document_data: Optional[list] = None
) -> dict:
    """
    Creates Firestore database (native mode) and optionally adds documents.
    """
    messages = []
    inserted_docs = []
    firestore_type = "firestore-native"
    document_data = document_data or []

    try:
        subprocess.run(f"gcloud services enable firestore.googleapis.com --project={project_id}", shell=True, check=True)
        messages.append("✅ Firestore API enabled.")

        subprocess.run(f"gcloud config set project {project_id}", shell=True, check=True)
        messages.append("✅ GCP project set.")

        check_cmd = f"gcloud firestore databases describe --database={db_name}"
        check_proc = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)

        db_exists = check_proc.returncode == 0

        if db_exists:
            messages.append(f"✅ Firestore DB '{db_name}' already exists.")
        else:
            create_cmd = (
                f"gcloud firestore databases create --database={db_name} "
                f"--location={location_id} --type={firestore_type}"
            )
            subprocess.run(create_cmd, shell=True, check=True)
            messages.append(f"✅ Firestore DB '{db_name}' created in {location_id}.")

        if collection_name and document_data:
            data_result = _add_documents(
                project_id,
                db_name,
                collection_name,
                document_data
            )
            messages.append(data_result["message"])
            inserted_docs.extend(data_result.get("inserted_documents", []))
        else:
            messages.append("ℹ️ No documents inserted. Provide `collection_name` and `document_data` to insert.")

        return {
            "status": "exists" if db_exists else "created",
            "message": "\n".join(messages),
            "inserted_documents": inserted_docs
        }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Command failed: {e.stderr or str(e)}"}
    except Exception as ex:
        return {"status": "error", "message": f"❌ Unexpected error: {str(ex)}"}


def _add_documents(
    project_id: str,
    db_name: str,
    collection_name: str,
    document_data: List[dict]
) -> dict:
    inserted_docs = []
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

        for idx, doc in enumerate(document_data):
            doc_copy = doc.copy()
            document_id = doc_copy.pop("doc_id", str(uuid.uuid4()))
            generated_id = "doc_id" not in doc

            fields = {}
            for key, value in doc_copy.items():
                if isinstance(value, bool):
                    fields[key] = {"booleanValue": value}
                elif isinstance(value, int):
                    fields[key] = {"integerValue": str(value)}
                elif isinstance(value, float):
                    fields[key] = {"doubleValue": value}
                elif isinstance(value, str) and value.endswith("Z") and "T" in value:
                    fields[key] = {"timestampValue": value}
                else:
                    fields[key] = {"stringValue": str(value)}

            url = (
                f"https://firestore.googleapis.com/v1/projects/{project_id}/"
                f"databases/{db_name}/documents/{collection_name}/{document_id}"
            )

            response = requests.patch(url, headers=headers, json={"fields": fields})
            if response.status_code in (200, 201):
                doc_name = response.json().get("name", "unknown").split("/")[-1]
                inserted_docs.append(doc_name)
                messages.append(f"✅ Document '{doc_name}' inserted/updated.")
                if generated_id:
                    messages.append(f"ℹ️ Generated random document ID: {doc_name}")
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



import subprocess
import requests
import json
from datetime import datetime, timedelta
import zoneinfo
from google.adk.tools import FunctionTool


def patch_document_field(doc_name, field_name, timestamp_iso, headers):
    """
    Patch a single Firestore document to add/update a timestamp field.
    """
    patch_url = f"https://firestore.googleapis.com/v1/{doc_name}?updateMask.fieldPaths={field_name}"
    patch_body = {
        "fields": {
            field_name: {
                "timestampValue": timestamp_iso
            }
        }
    }
    resp = requests.patch(patch_url, headers=headers, data=json.dumps(patch_body))
    return resp.status_code, resp.text


@FunctionTool
def set_ttl(
    project_id: str,
    db_name: str,
    collection_name: str,
    ttl_field: str
) -> dict:
    """
    Sets TTL policy on a Firestore collection. If the given TTL field is missing or invalid
    in any document, prompts the user to add a fallback 'expiresAt' field.
    """
    NY_TZ = zoneinfo.ZoneInfo("America/New_York")
    fallback_field = "expiresAt"
    messages = []

    try:
        # Step 1: Verify Firestore DB
        check_cmd = f"gcloud firestore databases describe --project={project_id} --database={db_name}"
        check_proc = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if check_proc.returncode != 0:
            return {
                "status": "error",
                "message": f"❌ Firestore DB '{db_name}' does not exist in project '{project_id}'."
            }

        # Step 2: Get access token
        token_proc = subprocess.run(
            "gcloud auth print-access-token", shell=True, check=True, capture_output=True
        )
        token = token_proc.stdout.decode("utf-8").strip()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Step 3: Fetch documents (limit 100 for now)
        url = (
            f"https://firestore.googleapis.com/v1/projects/{project_id}/"
            f"databases/{db_name}/documents/{collection_name}?pageSize=100"
        )
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"status": "error", "message": f"❌ Failed to fetch documents: {response.text}"}

        docs = response.json().get("documents", [])
        missing_or_invalid = []

        for doc in docs:
            fields = doc.get("fields", {})
            ttl_key = next((k for k in fields if k.lower() == ttl_field.lower()), None)
            is_valid = (
                ttl_key and "timestampValue" in fields.get(ttl_key, {}) and fields[ttl_key]["timestampValue"]
            )
            if not is_valid:
                missing_or_invalid.append(doc)

        # Step 4: Ask user for fallback TTL if needed
        if missing_or_invalid:
            return {
                "status": "ask_use_fallback",
                "message": (
                    f"⚠️ Field '{ttl_field}' is missing or invalid in {len(missing_or_invalid)} documents.\n"
                    "Do you want to apply a fallback TTL by adding a field `expiresAt` to all documents?\n"
                    "If yes, how many days from now should the documents expire?"
                ),
                "next_step_hint": {
                    "set_param": "ttl_field",
                    "options": [fallback_field],
                    "ask_param": "ttl_days",
                    "ask_message": "Enter number of days until expiration for fallback TTL field 'expiresAt'."
                }
            }
# f"--field-path={ttl_field} "
        # Step 5: Enable TTL on the given field
        ttl_cmd = (
            f"gcloud firestore fields ttls update expiresAt "
            f"--project={project_id} "
            f"--collection-group={collection_name} "
            
            f"--enable-ttl "
            # f"--async"
        )

        subprocess.run(ttl_cmd, shell=True, check=True)
        messages.append(f"✅ TTL policy enabled on field '{ttl_field}' in collection '{collection_name}'.")

        return {"status": "success", "message": "\n".join(messages)}

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ CLI command failed: {e.stderr or str(e)}"}
    except Exception as ex:
        return {"status": "error", "message": f"❌ Unexpected error: {str(ex)}"}

def get_tools():
    return [create_firestore_db, set_ttl]
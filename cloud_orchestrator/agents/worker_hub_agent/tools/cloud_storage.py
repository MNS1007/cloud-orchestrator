import json
import subprocess
from google.adk.tools.function_tool import FunctionTool

# TODO:
# 1. Add validation for key_name in set_default_encryption
# 2. Add validation for lifecycle_policy in set_lifecycle_rule
# 3. Add validation for num_newer_versions in set_lifecycle_rule
# 4. Add validation for expire_after_days in set_lifecycle_rule
# 5. Add validation for storage_class in set_default_storage_class
# 6. Add validation for terminal_class in enable_autoclass


@FunctionTool
def create_bucket(
    project_id: str, 
    bucket_name: str, 
    location: str
) -> dict:
    """
    Creates a Google Cloud Storage bucket in the specified location.
    Location examples: US, US-CENTRAL1, EUROPE-WEST1, ASIA-SOUTHEAST1, etc.
    """
    try:
        subprocess.run(
            f"gcloud storage buckets create gs://{bucket_name} "
            f"--location={location} --project={project_id}",
            shell=True,
            check=True,
        )
        return {"message": f"✅ Bucket '{bucket_name}' created in '{location}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to create bucket: {e}"}

@FunctionTool
def enable_versioning(
    bucket_name: str
) -> dict:
    try:
        subprocess.run(
            f"gcloud storage buckets update gs://{bucket_name} --versioning",
            shell=True,
            check=True,
        )
        return {"message": f"✅ Versioning enabled on '{bucket_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to enable versioning: {e}"}

@FunctionTool
def upload_to_bucket(
    bucket_name: str, 
    local_file_path: str, 
    remote_path: str = ""
) -> dict:
    """
    Uploads a local file to a GCS bucket.
    """
    try:
        subprocess.run(
            f"gcloud storage cp {local_file_path} gs://{bucket_name}/{remote_path}",
            shell=True,
            check=True,
        )
        return {
            "message": f"✅ File '{local_file_path}' uploaded to 'gs://{bucket_name}/{remote_path}'"
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Upload failed: {e}"
        }

@FunctionTool
def set_default_storage_class(
    bucket_name: str, 
    storage_class: str
) -> dict:
    """
    Sets the default storage class for a bucket.
    """
    try:
        subprocess.run(
            f"gcloud storage buckets update gs://{bucket_name} "
            f"--default-storage-class={storage_class.upper()}",
            shell=True,
            check=True,
        )
        return {"message": f"✅ Default storage class set to '{storage_class.upper()}' for bucket '{bucket_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to set storage class: {e}"}

@FunctionTool
def enable_soft_delete(
    bucket_name: str, 
    duration: str = "10d"
) -> dict:
    """
    Enables soft delete with a specified duration (e.g., '10d' for 10 days).
    """
    try:
        subprocess.run(
            f"gcloud storage buckets update gs://{bucket_name} "
            f"--soft-delete-duration={duration}",
            shell=True,
            check=True,
        )
        return {"message": f"🕒 Soft delete enabled with duration '{duration}' on bucket '{bucket_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to enable soft delete: {e}"}

@FunctionTool
def enable_autoclass(
    bucket_name: str, 
    terminal_class: str = "ARCHIVE"
) -> dict:
    """
    Enables Autoclass and sets the terminal storage class (e.g., ARCHIVE).
    """
    try:
        subprocess.run(
            f"gcloud storage buckets update gs://{bucket_name} "
            f"--enable-autoclass "
            f"--autoclass-terminal-storage-class={terminal_class.upper()}",
            shell=True,
            check=True,
        )
        return {"message": f"✅ Autoclass enabled with terminal class '{terminal_class.upper()}' for '{bucket_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to enable Autoclass: {e}"}

@FunctionTool
def set_uniform_access(
    bucket_name: str, 
    enable: bool = True
) -> dict:
    """
    Enables or disables uniform bucket-level access.
    """
    try:
        flag = "--uniform-bucket-level-access" if enable else "--no-uniform-bucket-level-access"
        subprocess.run(
            f"gcloud storage buckets update gs://{bucket_name} {flag}",
            shell=True,
            check=True,
        )
        state = "enabled" if enable else "disabled"
        return {"message": f"✅ Uniform bucket-level access {state} on '{bucket_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to update uniform access: {e}"}

@FunctionTool
def set_public_access_prevention(
    bucket_name: str, 
    prevent: bool = True
) -> dict:
    """
    Enables or disables public access prevention on the bucket.
    """
    try:
        flag = "--pap" if prevent else "--no-pap"
        subprocess.run(
            f"gcloud storage buckets update gs://{bucket_name} {flag}",
            shell=True,
            check=True,
        )
        state = "enabled" if prevent else "disabled"
        return {"message": f"🔐 Public access prevention {state} for '{bucket_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to set public access prevention: {e}"}

@FunctionTool
def set_default_encryption(
    bucket_name: str, 
    key_name: str
) -> dict:
    """
    Sets a customer-managed encryption key (CMEK) as default for the bucket.
    Example key format: projects/my-project/locations/global/keyRings/my-kr/cryptoKeys/my-key
    """
    try:
        subprocess.run(
            f"gcloud storage buckets update gs://{bucket_name} "
            f"--default-encryption-key={key_name}",
            shell=True,
            check=True,
        )
        return {"message": f"🔐 Default encryption key set for '{bucket_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to set encryption key: {e}"}
# Key Name Validation (for set_default_encryption)
# You accept key_name in this format:
# projects/my-project/locations/global/keyRings/my-kr/cryptoKeys/my-key
# 👉 This should be validated or documented more explicitly to avoid user errors.


@FunctionTool
def set_lifecycle_rule(
    bucket_name: str,
    num_newer_versions: int = 1,
    expire_after_days: int = 3
) -> dict:
    """
    Sets lifecycle rules to delete non-current versions of objects
    after a given number of days, keeping a certain number of versions.
    """
    try:
        lifecycle_policy = {
            "rule": [
                {
                    "action": {"type": "Delete"},
                    "condition": {
                        "numNewerVersions": num_newer_versions,
                        "age": expire_after_days
                    },
                }
            ]
        }

        lifecycle_json = json.dumps(lifecycle_policy)

        subprocess.run(
            f"echo '{lifecycle_json}' | gcloud storage buckets update gs://{bucket_name} --lifecycle-file=-",
            shell=True,
            check=True,
        )

        # lifecycle_policy = {...}
        # lifecycle_json = json.dumps(lifecycle_policy)

        # subprocess.run(
        #     ["gcloud", "storage", "buckets", "update", f"gs://{bucket_name}", "--lifecycle-file=-"],
        #     input=lifecycle_json.encode(),
        #     check=True
        # )

        return {
            "message": f"✅ Lifecycle rule applied to '{bucket_name}': "
                       f"Keep {num_newer_versions} version(s), expire non-current after {expire_after_days} day(s)."
        }
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to set lifecycle rule: {e}"}


# | **Function**                                              | **Parameter(s)**     | **Valid Values / Examples**                                                       |
# | --------------------------------------------------------- | -------------------- | --------------------------------------------------------------------------------- |
# | `create_bucket`                                           | `project_id`         | Your GCP project ID (e.g., `my-project-123`)                                      |
# |                                                           | `bucket_name`        | Globally unique bucket name (e.g., `my-bucket-01`)                                |
# |                                                           | `location`           | `US`, `EU`, `ASIA`, `US-CENTRAL1`, `EUROPE-WEST1`, etc.                           |
# | `enable_versioning`                                       | `bucket_name`        | Existing bucket name                                                              |
# | `upload_to_bucket`                                        | `bucket_name`        | Existing bucket name                                                              |
# |                                                           | `local_file_path`    | Absolute or relative path to file (e.g., `./test.jpg`)                            |
# |                                                           | `remote_path`        | Optional path inside bucket (e.g., `folder/file.jpg`)                             |
# | `set_default_storage_class`                               | `bucket_name`        | Existing bucket name                                                              |
# |                                                           | `storage_class`      | `STANDARD`, `NEARLINE`, `COLDLINE`, `ARCHIVE`                                     |
# | `set_uniform_bucket_level_access`<br>`set_uniform_access` | `bucket_name`        | Existing bucket name                                                              |
# |                                                           | `enable`             | `True` (enable), `False` (disable)                                                |
# | `enable_soft_delete`                                      | `bucket_name`        | Existing bucket name                                                              |
# |                                                           | `duration`           | Duration format like `10d`, `3d`, `1y`, `6m` (days, months, years)                |
# | `enable_autoclass`                                        | `bucket_name`        | Existing bucket name                                                              |
# |                                                           | `terminal_class`     | Must be one of: `STANDARD`, `ARCHIVE`, `COLDLINE`, `NEARLINE`                     |
# | `set_public_access_prevention`                            | `bucket_name`        | Existing bucket name                                                              |
# |                                                           | `prevent`            | `True` (enable), `False` (disable)                                                |
# | `set_default_encryption`                                  | `bucket_name`        | Existing bucket name                                                              |
# |                                                           | `key_name`           | Format: `projects/<project>/locations/global/keyRings/<keyring>/cryptoKeys/<key>` |
# | `set_lifecycle_rule`                                      | `bucket_name`        | Existing bucket name                                                              |
# |                                                           | `num_newer_versions` | Integer ≥ 0 (e.g., `1`, `3`)                                                      |
# |                                                           | `expire_after_days`  | Integer ≥ 1 (e.g., `3`, `7`, `30`)                                                |
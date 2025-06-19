import os
import subprocess
from google.adk.tools.function_tool import FunctionTool
import platform

#install cloud_sql_agent

# ⚙️ Utility / Custom Operations

@FunctionTool
def run_psql_query(
    instance_name: str,
    db_name: str,
    password: str,
    query: str,
    user: str = "postgres"
) -> dict:
    """
    Executes a SQL query on a Cloud SQL PostgreSQL instance using psql.
    Automatically fetches the public IP of the instance and, if necessary,
    authorizes the client's current public IP address to connect.
    """
    try:
        # Step 1: Get Cloud SQL instance's public IP
        instance_host_output = subprocess.check_output(
            f'gcloud sql instances describe {instance_name} --format="value(ipAddresses[0].ipAddress)"',
            shell=True,
            text=True
        ).strip()

        instance_host = instance_host_output if instance_host_output else None
        print("Cloud SQL Instance Host IP:", instance_host)
        if not instance_host:
            return {"error": "❌ No public IP found for the instance. Is it configured for external connections?"}

        # Step 2: Get the client's (your machine's) public IP address
        # Using platform.system() to adjust curl command if needed (though curl is usually cross-platform)
        try:
            # Use a reliable service to get external IP
            client_public_ip = subprocess.check_output(
                'curl -s ifconfig.me', # -s for silent output
                shell=True,
                text=True
            ).strip()
            print("Client Public IP:", client_public_ip)
            if not client_public_ip:
                return {"error": "❌ Could not determine client's public IP address."}
        except Exception as e:
            return {"error": f"❌ Failed to get client's public IP: {str(e)}"}

        # Step 3: Authorize the client's public IP in Cloud SQL
        # First, get existing authorized networks to avoid overwriting them
        try:
            existing_networks_output = subprocess.check_output(
                f'gcloud sql instances describe {instance_name} --format="value(settings.ipConfiguration.authorizedNetworks[].value)"',
                shell=True,
                text=True
            ).strip()
            # Split by newline and filter out empty strings, then join with comma
            existing_networks = [net.strip() for net in existing_networks_output.split('\n') if net.strip()]
        except subprocess.CalledProcessError:
            existing_networks = [] # No existing networks or error fetching them

        # Add the client's current IP if not already in the list
        client_ip_with_cidr = f"{client_public_ip}/32"
        if client_ip_with_cidr not in existing_networks:
            print(f"Authorizing client IP: {client_public_ip}...")
            all_networks = existing_networks + [client_ip_with_cidr]
            networks_string = ",".join(all_networks)

            try:
                subprocess.run(
                    f"gcloud sql instances patch {instance_name} --authorized-networks=\"{networks_string}\"",
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"✅ Client IP {client_public_ip} authorized successfully.")
            except subprocess.CalledProcessError as e:
                return {
                    "error": f"❌ Failed to authorize client IP {client_public_ip}. Ensure your gcloud user has 'cloudsql.instances.update' permission. Stderr: {e.stderr}",
                    "stdout": e.stdout
                }
        else:
            print(f"Client IP {client_public_ip} is already authorized.")


        # Step 4: Set password env variable
        env = os.environ.copy()
        env["PGPASSWORD"] = password

        # Step 5: Run query using psql
        # Handle double quotes within the query for shell execution
        # Also ensure the command uses the instance_host (Cloud SQL's public IP)
        command = f'psql -h {instance_host} -U {user} -d {db_name} -c "{query}"'

        print(f"Executing psql command: {command}")

        result = subprocess.run(
            command,
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            check=False # Do not raise CalledProcessError for non-zero exit codes; handle manually
        )
        print("psql result:", result)

        if result.returncode == 0:
            return {
                "message": "✅ Query executed successfully.",
                "stdout": result.stdout
            }
        else:
            return {
                "error": "❌ Query failed.",
                "stderr": result.stderr,
                "stdout": result.stdout
            }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Command execution failed. Stderr: {e.stderr}",
            "stdout": e.stdout
        }
    except Exception as ex:
        return {"error": f"⚠️ Unexpected error: {str(ex)}"}

# ✅ Section 1: Managing Instances

@FunctionTool
def create_sql_instance(
    project_id: str,
    instance_name: str,
    zone: str,
    cpu: int,
    memory_mb: int,
    root_password: str,
    edition: str,
    db_version: str
) -> dict:
    """
    Creates a Cloud SQL PostgreSQL instance with user-specified configuration.
    """
    try:
        subprocess.run(
            f"gcloud sql instances create {instance_name} "
            f"--database-version={db_version} "
            f"--zone={zone} "
            f"--cpu={cpu} "
            f"--memory={memory_mb}MB "
            f"--root-password={root_password} "
            f"--edition={edition} "
            f"--project={project_id}",
            shell=True,
            check=True,
        )
        return {"message": f"✅ Cloud SQL instance '{instance_name}' created in zone '{zone}' with {cpu} CPU and {memory_mb}MB memory."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Instance creation failed: {e}"}

@FunctionTool
def connect_to_sql_instance(
    instance_name: str,
    db_name : str
) -> dict:
    """
    Launches interactive connection to Cloud SQL via psql (user must enter password).
    """
    user = "postgres"
    try:
        subprocess.run(
            f"gcloud sql connect {instance_name} --user={user} --database={db_name}",
            shell=True,
        )
        
        return {"message": f"🔗 Connected to instance '{instance_name}' as '{user}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to connect via psql: {e}"}

@FunctionTool
def describe_sql_instance(instance_name: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud sql instances describe {instance_name}",
            shell=True,
            text=True
        )
        return {"description": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def list_sql_instances() -> dict:
    try:
        output = subprocess.check_output(
            "gcloud sql instances list",
            shell=True,
            text=True
        )
        return {"instances": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def delete_sql_instance(instance_name: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql instances delete {instance_name} --quiet",
            shell=True,
            check=True
        )
        return {"message": f"🗑️ Instance '{instance_name}' deleted successfully."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def update_sql_instance(instance_name: str, update_flags: str) -> dict:
    """
    update_flags: Additional flags like --cpu=2 --memory=4GB
    """
    try:
        subprocess.run(
            f"gcloud sql instances patch {instance_name} {update_flags}",
            shell=True,
            check=True
        )
        return {"message": f"🔄 Instance '{instance_name}' updated with flags: {update_flags}"}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def restart_sql_instance(instance_name: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql instances restart {instance_name}",
            shell=True,
            check=True
        )
        return {"message": f"🔁 Instance '{instance_name}' restarted."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def reschedule_sql_maintenance(instance_name: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql instances reschedule-maintenance {instance_name} --reschedule-type=IMMEDIATE",
            shell=True,
            check=True
        )
        return {"message": f"🛠️ Maintenance rescheduled for instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# ✅ Section 2: Managing Databases

@FunctionTool
def create_sql_database(instance_name: str, database_name: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql databases create {database_name} --instance={instance_name}",
            shell=True,
            check=True
        )
        return {"message": f"📁 Database '{database_name}' created in instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def describe_sql_database(instance_name: str, database_name: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud sql databases describe {database_name} --instance={instance_name}",
            shell=True,
            text=True
        )
        return {"description": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def list_sql_databases(instance_name: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud sql databases list --instance={instance_name}",
            shell=True,
            text=True
        )
        return {"databases": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def delete_sql_database(instance_name: str, database_name: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql databases delete {database_name} --instance={instance_name} --quiet",
            shell=True,
            check=True
        )
        return {"message": f"🗑️ Database '{database_name}' deleted from instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def patch_sql_database(instance_name: str, database_name: str, patch_flags: str) -> dict:
    """
    patch_flags: Additional flags like --charset=utf8 --collation=utf8_general_ci
    """
    try:
        subprocess.run(
            f"gcloud sql databases patch {database_name} --instance={instance_name} {patch_flags}",
            shell=True,
            check=True
        )
        return {"message": f"🛠️ Database '{database_name}' patched with flags: {patch_flags}"}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# ✅ Section 3: Managing Users

@FunctionTool
def set_sql_password(
    instance_name: str,
    password: str
) -> dict:
    user = "postgres"
    """
    Sets or resets the password for a Cloud SQL user.
    """
    try:
        subprocess.run(
            f"gcloud sql users set-password {user} "
            f"--instance={instance_name} "
            f"--password={password}",
            shell=True,
            check=True,
        )
        return {"message": f"🔐 Password set for user '{user}' on instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": f"❌ Failed to set password: {e}"}

@FunctionTool
def create_sql_user(instance_name: str, username: str, password: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql users create {username} --instance={instance_name} --password={password}",
            shell=True,
            check=True
        )
        return {"message": f"👤 User '{username}' created on instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def delete_sql_user(instance_name: str, username: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql users delete {username} --instance={instance_name}",
            shell=True,
            check=True
        )
        return {"message": f"🗑️ User '{username}' deleted from instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def list_sql_users(instance_name: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud sql users list --instance={instance_name}",
            shell=True,
            text=True
        )
        return {"users": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# ✅ Section 4: Managing Backups

@FunctionTool
def create_sql_backup(instance_name: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql backups create --instance={instance_name}",
            shell=True,
            check=True
        )
        return {"message": f"📦 Backup initiated for instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def delete_sql_backup(instance_name: str, backup_id: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql backups delete {backup_id} --instance={instance_name} --quiet",
            shell=True,
            check=True
        )
        return {"message": f"🗑️ Backup '{backup_id}' deleted from instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def describe_sql_backup(instance_name: str, backup_id: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud sql backups describe {backup_id} --instance={instance_name}",
            shell=True,
            text=True
        )
        return {"backup_details": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def list_sql_backups(instance_name: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud sql backups list --instance={instance_name}",
            shell=True,
            text=True
        )
        return {"backups": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def restore_sql_instance(instance_name: str, backup_id: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql instances restore-backup {instance_name} --backup-id={backup_id}",
            shell=True,
            check=True
        )
        return {"message": f"♻️ Instance '{instance_name}' restored from backup '{backup_id}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# ✅ Section 5: Importing & Exporting Data

@FunctionTool
def export_sql_data(instance_name: str, gcs_uri: str, export_flags: str = "") -> dict:
    """
    gcs_uri: e.g. gs://your-bucket/your-file.sql
    export_flags: optional flags like --database=DB_NAME --offload
    """
    try:
        subprocess.run(
            f"gcloud sql export sql {instance_name} {gcs_uri} {export_flags}",
            shell=True,
            check=True
        )
        return {"message": f"📤 Data exported from '{instance_name}' to '{gcs_uri}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def import_sql_data(instance_name: str, gcs_uri: str, import_flags: str = "") -> dict:
    """
    gcs_uri: e.g. gs://your-bucket/your-file.sql
    import_flags: optional flags like --database=DB_NAME
    """
    try:
        subprocess.run(
            f"gcloud sql import sql {instance_name} {gcs_uri} {import_flags}",
            shell=True,
            check=True
        )
        return {"message": f"📥 Data imported to '{instance_name}' from '{gcs_uri}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# ✅ Section 6: Managing SSL Certificates

@FunctionTool
def create_sql_ssl_cert(instance_name: str, cert_name: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql ssl-certs create {cert_name} --instance={instance_name}",
            shell=True,
            check=True
        )
        return {"message": f"🔐 SSL cert '{cert_name}' created for instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def delete_sql_ssl_cert(instance_name: str, cert_name: str) -> dict:
    try:
        subprocess.run(
            f"gcloud sql ssl-certs delete {cert_name} --instance={instance_name}",
            shell=True,
            check=True
        )
        return {"message": f"🗑️ SSL cert '{cert_name}' deleted from instance '{instance_name}'."}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def describe_sql_ssl_cert(instance_name: str, cert_name: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud sql ssl-certs describe {cert_name} --instance={instance_name}",
            shell=True,
            text=True
        )
        return {"cert_description": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# ✅ Section 7: Monitoring Operations

@FunctionTool
def list_sql_ssl_certs(instance_name: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud sql ssl-certs list --instance={instance_name}",
            shell=True,
            text=True
        )
        return {"certs": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def list_sql_operations(instance_name: str) -> dict:
    try:
        output = subprocess.check_output(
            f"gcloud sql operations list --instance={instance_name}",
            shell=True,
            text=True
        )
        return {"operations": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


# ✅ Section 8: Miscellaneous Commands

@FunctionTool
def list_sql_tiers() -> dict:
    try:
        output = subprocess.check_output("gcloud sql tiers list", shell=True, text=True)
        return {"tiers": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def list_sql_flags() -> dict:
    try:
        output = subprocess.check_output("gcloud sql flags list", shell=True, text=True)
        return {"flags": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@FunctionTool
def generate_sql_login_token() -> dict:
    try:
        output = subprocess.check_output("gcloud sql generate-login-token", shell=True, text=True)
        return {"token": output}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}
    



# | **Function**                 | **Required Inputs**                                                                                 |
# | ---------------------------- | --------------------------------------------------------------------------------------------------- |
# * | `create_sql_instance`        | `project_id`, `instance_name`, `zone`, `cpu`, `memory_mb`, `root_password`, `edition`, `db_version` |
# | `describe_sql_instance`      | `instance_name`                                                                                     |
# | `list_sql_instances`         | *(none)*                                                                                            |
# | `delete_sql_instance`        | `instance_name`                                                                                     |
# | `update_sql_instance`        | `instance_name`, `update_flags`                                                                     |
# | `restart_sql_instance`       | `instance_name`                                                                                     |
# * | `connect_to_sql_instance`    | `instance_name`, `user`                                                                             |
# | `reschedule_sql_maintenance` | `instance_name`                                                                                     |
# | **Function**            | **Required Inputs**                             |
# | ----------------------- | ----------------------------------------------- |
# | `create_sql_database`   | `instance_name`, `database_name`                |
# | `describe_sql_database` | `instance_name`, `database_name`                |
# | `list_sql_databases`    | `instance_name`                                 |
# | `delete_sql_database`   | `instance_name`, `database_name`                |
# | `patch_sql_database`    | `instance_name`, `database_name`, `patch_flags` |
# | **Function**       | **Required Inputs**                     |
# | ------------------ | --------------------------------------- |
# | `create_sql_user`  | `instance_name`, `username`, `password` |
# | `delete_sql_user`  | `instance_name`, `username`             |
# | `list_sql_users`   | `instance_name`                         |
# * | `set_sql_password` | `instance_name`, `user`, `password`     |
# | **Function**           | **Required Inputs**          |
# | ---------------------- | ---------------------------- |
# | `create_sql_backup`    | `instance_name`              |
# | `delete_sql_backup`    | `instance_name`, `backup_id` |
# | `describe_sql_backup`  | `instance_name`, `backup_id` |
# | `list_sql_backups`     | `instance_name`              |
# | `restore_sql_instance` | `instance_name`, `backup_id` |
# | **Function**      | **Required Inputs**                                     |
# | ----------------- | ------------------------------------------------------- |
# | `export_sql_data` | `instance_name`, `gcs_uri`, *(optional)* `export_flags` |
# | `import_sql_data` | `instance_name`, `gcs_uri`, *(optional)* `import_flags` |
# | **Function**            | **Required Inputs**          |
# | ----------------------- | ---------------------------- |
# | `create_sql_ssl_cert`   | `instance_name`, `cert_name` |
# | `delete_sql_ssl_cert`   | `instance_name`, `cert_name` |
# | `describe_sql_ssl_cert` | `instance_name`, `cert_name` |
# | `list_sql_ssl_certs`    | `instance_name`              |
# | **Function**          | **Required Inputs** |
# | --------------------- | ------------------- |
# | `list_sql_operations` | `instance_name`     |
# | **Function**               | **Required Inputs** |
# | -------------------------- | ------------------- |
# | `list_sql_tiers`           | *(none)*            |
# | `list_sql_flags`           | *(none)*            |
# | `generate_sql_login_token` | *(none)*            |
# | **Function**     | **Required Inputs**                            |
# | ---------------- | ---------------------------------------------- |
# * | `run_psql_query` | `db_name`, `user`, `password`, `host`, `query` |
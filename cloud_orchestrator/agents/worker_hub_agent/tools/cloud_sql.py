import os
import subprocess
from google.adk.tools.function_tool import FunctionTool
import platform

#install cloud_sql_agent

# input 
# 'root_password": "password",
# "zone": "us-central1-a",
# "memory_mb": 7680,
# "instance_name": "give_new_name",
# "project_id": "your_project_id",
# "db_version": "POSTGRES_17",
# "cpu": 2,
# "edition": "ENTERPRISE"
# make sure you enter valid inputs

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
def set_sql_password(
    instance_name: str,
    user: str,
    password: str
) -> dict:
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
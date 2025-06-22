from google.adk.tools import FunctionTool
import subprocess
import json
from typing import Optional

@FunctionTool
def manage_vpc_network(
    vpc_name: str,
    project_id: str,
    create_subnets: bool = False,
    subnets: Optional[list] = None,
    list_subnets: bool = False
) -> dict:
    """
    Manages VPC creation and subnet addition in a GCP project.

    - Enables Compute Engine API
    - Checks if the VPC exists.
    - Optionally lists subnets in the VPC (when list_subnets=True)
    - Optionally adds subnets.
    - Creates the VPC if it doesn't exist.
    """
    try:
        subprocess.run(
            f"gcloud services enable compute.googleapis.com --project {project_id}",
            check=True, shell=True
        )
        print("✅ Compute Engine API enabled successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Failed to enable Compute Engine API.")
        return {"status": "error", "message": f"Failed to enable Compute Engine API. Details: {e}"}

    try:
        print(f"🔍 Checking if VPC '{vpc_name}' exists...")
        result = subprocess.run(
            f"gcloud compute networks describe {vpc_name} --project {project_id}",
            shell=True, capture_output=True
        )

        if result.returncode == 0:
            print(f"✅ VPC '{vpc_name}' exists.")
            msg = f"✅ VPC '{vpc_name}' already exists."

            if list_subnets:
                print(f"🔍 Listing subnets in VPC '{vpc_name}'...")
                try:
                    cmd = (
                        f"gcloud compute networks subnets list "
                        f"--filter=network:{vpc_name} "
                        f"--project={project_id} "
                        f"--format=json"
                    )
                    subnets_result = subprocess.run(cmd, shell=True, capture_output=True, check=True)
                    output = subnets_result.stdout.decode().strip()
                    print("Raw subnets output:", output)  # Debug print

                    existing_subnets = json.loads(output or "[]")
                    print(f"✅ Found {len(existing_subnets)} subnets in VPC '{vpc_name}'.")

                    if not existing_subnets:
                        return {"status": "empty", "message": f"ℹ️ No subnets present in VPC '{vpc_name}'."}
                    else:
                        formatted = [
                            {
                                "name": s['name'],
                                "region": s['region'].split('/')[-1],
                                "range": s['ipCidrRange']
                            } for s in existing_subnets
                        ]

                        # Format a message string listing the subnets (for Google ADK UI)
                        subnet_lines = [
                            f"- {s['name']} (Region: {s['region']}, Range: {s['range']})"
                            for s in formatted
                        ]
                        subnet_message = f"✅ Found {len(formatted)} subnets in VPC '{vpc_name}':\n" + "\n".join(subnet_lines)

                        # Print subnet list to terminal
                        print(subnet_message)

                        # Return message with subnet list for UI
                        return {
                            "status": "success",
                            "message": subnet_message,
                            "subnets": formatted
                        }
                except subprocess.CalledProcessError as e:
                    print("❌ Failed to list subnets in VPC.")
                    return {"status": "error", "message": f"Failed to list subnets. Details: {e}"}

            if create_subnets and subnets:
                print(f"➕ Creating subnets in VPC '{vpc_name}'...")
                print(subnets)
                try:
                    for subnet in subnets:
                        expected_keys = {"name", "region", "range"}
                        if set(subnet.keys()) != expected_keys:
                            return {
                                "status": "error",
                                "message": (
                                    f"Invalid subnet format: {subnet}. Each subnet must contain ONLY "
                                    f"these keys: 'name', 'region', 'range'. No extras or alternate names allowed."
                                )
                            }
                        
                        subprocess.run(
                            f"gcloud compute networks subnets create {subnet['name']} "
                            f"--network {vpc_name} --region {subnet['region']} "
                            f"--range {subnet['range']} --project {project_id}",
                            shell=True, check=True
                        )
                    print("✅ Subnets created successfully.")
                    return {"status": "success", "message": f"{msg} Subnets created successfully."}
                except subprocess.CalledProcessError as e:
                    print("❌ Failed to create subnets.")
                    return {"status": "error", "message": f"{msg} Failed to create subnets. Details: {e}"}
            else:
                return {"status": "exists", "message": f"{msg} Use create_subnets=True to add subnets."}

        # VPC doesn't exist — create it
        print(f"➕ VPC '{vpc_name}' not found, creating it now...")
        subprocess.run(
            f"gcloud compute networks create {vpc_name} --subnet-mode=custom "
            f"--bgp-routing-mode=regional --project {project_id}",
            check=True, shell=True
        )
        print("✅ VPC created.")
        msg = f"✅ VPC '{vpc_name}' created successfully."

        if create_subnets and subnets:
            print("➕ Creating subnets in new VPC...")
            try:
                for subnet in subnets:
                    subprocess.run(
                        f"gcloud compute networks subnets create {subnet['name']} "
                        f"--network {vpc_name} --region {subnet['region']} "
                        f"--range {subnet['range']} --project {project_id}",
                        shell=True, check=True
                    )
                print("✅ Subnets created successfully.")
                return {"status": "success", "message": f"{msg} Subnets created successfully."}
            except subprocess.CalledProcessError as e:
                print("❌ Failed to create subnets.")
                return {"status": "error", "message": f"{msg} Failed to create subnets. Details: {e}"}
        else:
            return {"status": "created", "message": f"{msg} Use create_subnets=True to add subnets."}

    except subprocess.CalledProcessError as e:
        print("❌ Operation failed.")
        return {"status": "error", "message": f"Operation failed. Details: {e}"}


from typing import List, Dict

@FunctionTool
def check_network_subnets(
    subnets: List[Dict[str, str]],  # list of {"name": subnet_name, "region": subnet_region}
    project_id: str
) -> dict:
    """
    Checks whether multiple subnets belong to the same VPC network.

    Args:
        subnets (List[Dict[str, str]]): A list of dictionaries with 'name' and 'region' keys for each subnet.
        project_id (str): The Google Cloud project ID.

    Returns:
        dict: Status and a detailed message indicating which subnets belong to which VPC.
    """
    try:
        networks_map = {}  # network_name -> list of subnets

        for subnet in subnets:
            name = subnet["name"]
            region = subnet["region"]
            result = subprocess.run(
                f"gcloud compute networks subnets describe {name} "
                f"--region {region} --project {project_id} --format=json",
                shell=True,
                check=True,
                capture_output=True
            )
            subnet_info = json.loads(result.stdout)
            network = subnet_info["network"].split("/")[-1]
            networks_map.setdefault(network, []).append(f"{name} (region: {region})")

        if len(networks_map) == 1:
            network_name = next(iter(networks_map))
            return {
                "status": "connected",
                "message": f"✅ All subnets belong to the same VPC '{network_name}': {networks_map[network_name]}"
            }
        else:
            details = "\n".join(
                f"VPC '{net}': {subs}"
                for net, subs in networks_map.items()
            )
            return {
                "status": "isolated",
                "message": f"⚠️ Subnets belong to different VPCs:\n{details}"
            }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Failed to check subnets. Details: {e}"}


@FunctionTool
def add_serverless_connector(
    connector_name: str,
    vpc_network: str,
    region: str,
    ip_range: str,
    project_id: str
) -> dict:
    """
    Creates a VPC Serverless Connector for connecting Cloud Functions,
    App Engine, or Cloud Run to a VPC network.

    Args:
        connector_name (str): Name for the connector.
        vpc_network (str): Name of the VPC network to connect to.
        region (str): GCP region where the connector will be created.
        ip_range (str): CIDR range for the connector (e.g., 10.8.0.0/28).
        project_id (str): Google Cloud project ID.

    Returns:
        dict: Status and message indicating result of the operation.
    """
    try:
        # Enable VPC Access API
        subprocess.run(
            f"gcloud services enable vpcaccess.googleapis.com --project {project_id}",
            shell=True,
            check=True
        )

        # Create the connector
        subprocess.run(
            f"gcloud compute networks vpc-access connectors create {connector_name} "
            f"--network {vpc_network} "
            f"--region {region} "
            f"--range {ip_range} "
            f"--project {project_id}",
            shell=True,
            check=True
        )

        return {
            "status": "success",
            "message": f"✅ Connector '{connector_name}' created successfully in region '{region}'."
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"❌ Failed to create connector '{connector_name}'. Details: {e}"
        }



def get_tools():
    return [manage_vpc_network, check_network_subnets, add_serverless_connector]

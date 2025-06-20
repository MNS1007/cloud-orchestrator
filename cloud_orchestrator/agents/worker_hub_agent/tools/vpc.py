from google.adk.tools import FunctionTool
import subprocess
import json
from typing import Optional

@FunctionTool
def manage_vpc_network(
    vpc_name: str,
    project_id: str,
    create_subnets: bool = False,
    subnets: Optional[list] = None
) -> dict:
    """
    Manages VPC creation and subnet addition in a GCP project.

    - Checks if the VPC exists.
    - If it exists, offers to add subnets.
    - If it does not exist, creates the VPC and optionally adds subnets.

    Args:
        vpc_name (str): Name of the VPC network.
        project_id (str): Google Cloud project ID.
        create_subnets (bool): Whether to proceed with subnet creation.
        subnets (list): Optional list of subnet dicts (name, range, region).

    Returns:
        dict: Status and messages about VPC and subnets.
    """
    try:
        # Step 1: Check if VPC exists
        result = subprocess.run(
            f"gcloud compute networks describe {vpc_name} --project {project_id}",
            shell=True,
            capture_output=True
        )

        if result.returncode == 0:
            # VPC already exists
            msg = f"✅ VPC '{vpc_name}' already exists."
            if create_subnets and subnets:
                # Add subnets to existing VPC
                try:
                    for subnet in subnets:
                        name = subnet["name"]
                        ip_range = subnet["range"]
                        region = subnet["region"]

                        subprocess.run(
                            f"gcloud compute networks subnets create {name} "
                            f"--network {vpc_name} --region {region} "
                            f"--range {ip_range} --project {project_id}",
                            shell=True,
                            check=True
                        )
                    return {"status": "success", "message": f"{msg} Subnets created successfully."}
                except subprocess.CalledProcessError as e:
                    return {"status": "error", "message": f"{msg} ❌ Failed to create subnets. Details: {e}"}
            else:
                return {
                    "status": "exists",
                    "message": f"{msg} Do you want to add subnets? Set `create_subnets=True` and pass the `subnets` list."
                }

        # Step 2: If VPC doesn't exist, create it
        subprocess.run(
            f"gcloud services enable compute.googleapis.com --project {project_id}",
            check=True,
            shell=True
        )

        subprocess.run(
            f"gcloud compute networks create {vpc_name} "
            f"--subnet-mode=custom --bgp-routing-mode=regional "
            f"--project {project_id}",
            check=True,
            shell=True
        )
        msg = f"✅ VPC '{vpc_name}' created successfully."

        if create_subnets and subnets:
            try:
                for subnet in subnets:
                    name = subnet["name"]
                    ip_range = subnet["range"]
                    region = subnet["region"]

                    subprocess.run(
                        f"gcloud compute networks subnets create {name} "
                        f"--network {vpc_name} --region {region} "
                        f"--range {ip_range} --project {project_id}",
                        shell=True,
                        check=True
                    )
                return {"status": "success", "message": f"{msg} Subnets created successfully."}
            except subprocess.CalledProcessError as e:
                return {"status": "error", "message": f"{msg} ❌ Failed to create subnets. Details: {e}"}
        else:
            return {
                "status": "created",
                "message": f"{msg} Do you want to add subnets? Set `create_subnets=True` and pass the `subnets` list."
            }

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"❌ Operation failed. Details: {e}"}



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


def get_tools():
    return [manage_vpc_network, check_network_subnets]

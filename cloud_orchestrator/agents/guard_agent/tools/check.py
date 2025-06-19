import subprocess
import json
from typing import Dict, Tuple
from google.adk.tools.function_tool import FunctionTool


@FunctionTool
def check_budget(project_id: str, billing_account_id: str) -> dict:
    """
    Verifies the project's daily/monthly spend against the active Budgets API entry.
    Returns one of: OK / WARN / BLOCK based on spend ratio.
    """
    import subprocess
    import json

    try:
        # Step 1: Resolve project number from ID
        number_result = subprocess.run([
            "gcloud", "projects", "describe", project_id,
            "--format=value(projectNumber)"
        ], check=True, stdout=subprocess.PIPE)
        project_number = number_result.stdout.decode().strip()
        full_project_ref = f"projects/{project_number}"

        # Step 2: Enable billingbudgets API (safe to re-run)
        subprocess.run([
            "gcloud", "services", "enable", "billingbudgets.googleapis.com",
            "--project", project_id
        ], check=True)

        # Step 3: List budgets under billing account
        result = subprocess.run([
            "gcloud", "billing", "budgets", "list",
            "--billing-account", billing_account_id,
            "--format=json"
        ], check=True, stdout=subprocess.PIPE)


        budgets = json.loads(result.stdout)

        if not budgets:
            return {
                "status": "WARN",
                "message": f"⚠️ No budgets found for billing account '{billing_account_id}'."
            }

        # Step 4: Match budgets that apply to the project (or to all projects)
        matched_budgets = []
        for budget in budgets:
            projects = budget.get("budgetFilter", {}).get("projects", [])
            if not projects or full_project_ref in projects:
                matched_budgets.append(budget)
        
        def create_budget_if_missing():
            create_cmd = [
                "gcloud", "billing", "budgets", "create",
                f"--billing-account={billing_account_id}",
                f"--display-name=AutoBudget-{project_id}",
                f"--budget-amount=10USD",
                f"--calendar-period=month",
                "--format=json"
            ]
            subprocess.run(create_cmd, check=True)

        if not matched_budgets:
            try:
                create_budget_if_missing()
                return {
                    "status": "WARN",
                    "message": f"⚠️ No budget was found for project `{project_id}`. Auto-created a $10/day budget (billing-wide). Please review it in the GCP Console."
                }
            except subprocess.CalledProcessError as create_err:
                return {
                    "status": "ERROR",
                    "message": (
                        f"❌ No budget found and failed to auto-create budget.\n"
                        f"Check permissions and ensure billingbudgets.googleapis.com is enabled.\n\n"
                        f"Details:\n{create_err}"
                    )
                }
            # Auto-create $10/day budget (scoped to billing account only)


        # Step 5: Analyze spend vs budget
        results = []
        for budget in matched_budgets:
            name = budget.get("displayName", "Unnamed Budget")
            amount = float(budget.get("amount", {}).get("specifiedAmount", {}).get("units", 0))
            spent = float(budget.get("amountSpent", {}).get("units", 0))
            ratio = spent / amount if amount > 0 else 0

            if ratio >= 1.0:
                results.append(f"❌ BLOCK: {name} exceeded — ${spent} / ${amount}")
            elif ratio >= 0.9:
                results.append(f"⚠️ WARN: {name} nearing limit — ${spent} / ${amount}")
            else:
                results.append(f"✅ OK: {name} usage is within limits — ${spent} / ${amount}")

        status = "BLOCK" if any("BLOCK" in r for r in results) else "WARN" if any("WARN" in r for r in results) else "OK"
        print('horse',status)
        print('horsemen',result)
        return {
            "status": status,
            "message": "\n".join(results)
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "ERROR",
            "message": f"❌ Failed to check budget: {e}"
        }

@FunctionTool
def fetch_budget_list(billing_account_id: str) -> Dict[str, Tuple[float, float]]:
    """
    Returns a dictionary of budgets under a billing account in the form:
    { "Budget Name": (limit_amount, spent_amount) }

    Uses `gcloud billing budgets list` under the hood.
    """
    try:
        result = subprocess.run([
            "gcloud", "billing", "budgets", "list",
            f"--billing-account={billing_account_id}",
            "--format=json"
        ], check=True, stdout=subprocess.PIPE)

        budgets = json.loads(result.stdout)
        if not budgets:
            return {}

        budget_dict = {}
        for budget in budgets:
            name = budget.get("displayName", "Unnamed Budget")
            limit = float(budget.get("amount", {}).get("specifiedAmount", {}).get("units", 0))
            spent = float(budget.get("amountSpent", {}).get("units", 0))
            budget_dict[name] = (limit, spent)

        return budget_dict

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to fetch budgets: {e}"
        }

@FunctionTool
def enable_service_api(project_id: str, service_name: str) -> dict:
    """
    Enables a specific GCP service API for a given project.

    Args:
        project_id: GCP project ID (e.g., "my-gcp-project")
        service_name: API service name (e.g., "compute.googleapis.com")

    Returns:
        dict with status and a message indicating success or failure
    """
    try:
        subprocess.run([
            "gcloud", "services", "enable", service_name,
            "--project", project_id
        ], check=True)

        return {
            "status": "OK",
            "message": f"✅ Successfully enabled API '{service_name}' for project '{project_id}'."
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "ERROR",
            "message": f"❌ Failed to enable API '{service_name}' for project '{project_id}'. Details: {e}"
        }

@FunctionTool
def check_quota(project_id: str, planned_usage: Dict[str, Dict[str, float]]) -> dict:
    """
    For Compute Engine, checks if planned usage (e.g., CPUs, INSTANCES) fits within quota
    for each specified region. Only supports compute.googleapis.com.
    Automatically enables the API if not already enabled.
    """
    import subprocess, json

    status_list = []
    details = []

    for service, region_map in planned_usage.items():
        if service != "compute.googleapis.com":
            details.append(f"⚠️ Service '{service}' not supported in this quota checker.")
            status_list.append("WARN")
            continue

        for region, metrics in region_map.items():
            try:
                result = subprocess.run([
                    "gcloud", "compute", "regions", "describe", region,
                    f"--project={project_id}",
                    "--format=json(quotas)"
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                quotas = json.loads(result.stdout).get("quotas", [])

                for metric_name, planned in metrics.items():
                    quota_entry = next((q for q in quotas if q.get("metric") == metric_name), None)

                    if not quota_entry:
                        details.append(f"⚠️ WARN: No quota entry found for {metric_name} in {region}")
                        status_list.append("WARN")
                        continue

                    limit = float(quota_entry.get("limit", 0))
                    usage = float(quota_entry.get("usage", 0))
                    remaining = limit - usage

                    if planned > limit:
                        details.append(f"❌ BLOCK: Planned {planned} exceeds total quota {limit} for {metric_name} in {region}")
                        status_list.append("BLOCK")
                    elif planned > remaining:
                        details.append(f"⚠️ WARN: Planned {planned} exceeds available quota {remaining} for {metric_name} in {region}")
                        status_list.append("WARN")
                    else:
                        details.append(f"✅ OK: Planned {planned} within quota ({usage}/{limit}) for {metric_name} in {region}")
                        status_list.append("OK")

            except subprocess.CalledProcessError as e:
                details.append(f"❌ ERROR: Failed to fetch quotas for '{region}' in project '{project_id}'. Stderr:\n{e.stderr}")
                status_list.append("ERROR")

    overall_status = "BLOCK" if "BLOCK" in status_list else "WARN" if "WARN" in status_list else "OK"

    return {
        "status": overall_status,
        "message": "\n".join(details)
    }

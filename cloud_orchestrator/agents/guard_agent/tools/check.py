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

def suggest_quota_increase(project_id: str, service: str, metric: str, region: str = None) -> str:
    """
    Builds a URL to request a quota increase in the GCP Console and returns a helpful message.
    
    Args:
        project_id: The GCP project ID.
        service: The full service name (e.g., compute.googleapis.com).
        metric: The quota metric name (e.g., CPUS).
        region: The region where quota is exceeded (optional).
    
    Returns:
        A user-friendly message with a console link.
    """
    base_url = "https://console.cloud.google.com/iam-admin/quotas"
    query_params = f"?project={project_id}&service={service}&metric={metric}"
    if region:
        query_params += f"&location={region}"

    full_url = f"{base_url}{query_params}"
    return (
        f"📌 To request a quota increase for `{metric}` in `{region or 'global'}`, visit:\n"
        f"{full_url}"
    )

@FunctionTool
def check_quota(project_id: str, planned_usage: Dict[str, Dict[str, Dict[str, float]]]) -> dict:
    """
    Checks if planned usage fits within quota for any GCP service using the Service Usage API.

    Requires: gcloud auth application-default login

    Args:
        project_id: GCP project ID
        planned_usage: Dict of service -> region -> metric -> planned value

    Returns:
        dict with overall status and quota comparison messages
    """
    import requests
    import subprocess
    import json

    def get_access_token():
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    status_list = []
    details = []

    for service, region_map in planned_usage.items():
        # Enable API
        try:
            subprocess.run(
                ["gcloud", "services", "enable", service, f"--project={project_id}"],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            details.append(f"🔧 Enabled API for {service}")
        except subprocess.CalledProcessError as e:
            if "already enabled" in e.stderr.lower():
                details.append(f"ℹ️ API {service} already enabled.")
            else:
                details.append(f"❌ BLOCK: Failed to enable API '{service}':\n{e.stderr}")
                status_list.append("BLOCK")
                continue

        # Fetch quotas
        url = f"https://serviceusage.googleapis.com/v1beta1/projects/{project_id}/services/{service}/consumerQuotaMetrics?view=FULL"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            details.append(f"❌ BLOCK: Failed to fetch quota for {service}: {response.text}")
            status_list.append("BLOCK")
            continue
        
        quota_data = response.json().get("metrics", [])

        for region, metrics in region_map.items():
            for metric, planned in metrics.items():
                matched = False
                for q in quota_data:
                    normalized_qmetric = q.get("metric", "").split("/")[-1].lower()
                    if metric.lower() == normalized_qmetric:
                        details.append("📊 MATCHED")
                        for limit in q.get("consumerQuotaLimits", []):
                            for bucket in limit.get("quotaBuckets", []):
                                is_global_quota = not bucket.get("dimensions") or "region" not in bucket["dimensions"]
                                bucket_region = bucket.get("dimensions", {}).get("region")
                                if bucket_region == region or is_global_quota:
                                    limit_val = float(bucket.get("effectiveLimit", 0))
                                    usage = float(bucket.get("usage", 0)) if "usage" in bucket else 0.0
                                    remaining = limit_val - usage
                                    if limit_val == -1:
                                        details.append(f"✅ OK: No enforced quota for {metric} in {region} (limit = -1)")
                                        status_list.append("OK")
                                    elif planned > limit_val:
                                        details.append(f"❌ BLOCK: {planned} > limit {limit_val} for {metric} in {region}")
                                        status_list.append("BLOCK")
                                        details.append(suggest_quota_increase(project_id, service, metric, region))
                                    elif planned > remaining:
                                        details.append(f"⚠️ WARN: {planned} > available {remaining} for {metric} in {region}")
                                        status_list.append("WARN")
                                    else:
                                        details.append(f"✅ OK: {planned} ≤ available {remaining} for {metric} in {region}")
                                        status_list.append("OK")

                                    matched = True
                                    break  # found region match, stop inner loop
                            if matched:
                                break  # matched one bucket, skip to next metric
                    if matched:
                        break
                if not matched:
                    details.append(f"⚠️ WARN: No match found for {metric} in {region}")
                    status_list.append("WARN")

    overall = "BLOCK" if "BLOCK" in status_list else "WARN" if "WARN" in status_list else "OK"
    return {
        "status": overall,
        "message": "\n".join(details)
    }

import os
import re
import ast
import json
import yaml
import pathlib
import google.generativeai as genai
from typing import Dict, List, Any
from google.adk.tools.function_tool import FunctionTool
import webbrowser

# Initialize Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Load capabilities catalog
_CAP_FILE = pathlib.Path(__file__).parents[2] / "capabilities.yaml"
CAPS = yaml.safe_load(open(_CAP_FILE))

# Utility to call LLM
def call_llm(prompt: str, model: str = "gemini-2.5-flash") -> str:
    llm = genai.GenerativeModel(model)
    response = llm.generate_content(prompt)
    return response.text.strip()

# ───────────────────────── visualize DAG ───────────────────────── #
@FunctionTool
def open_dag_page(parsed_response: dict, filename: str = "dag_visualization.html") -> Dict[str, str]:
    """
    Generate an HTML page rendering the DAG via Cytoscape and open it in a browser.
    Returns success or error message.
    """
    try:
        dag = parsed_response
        elements = []
        seen = set()
        for src, targets in dag.items():
            if src not in seen:
                elements.append({"data": {"id": src}})
                seen.add(src)
            for tgt in targets:
                if tgt not in seen:
                    elements.append({"data": {"id": tgt}})
                    seen.add(tgt)
                elements.append({"data": {"source": src, "target": tgt}})
        html = f"""
<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>GCP DAG</title>
<script src='https://unpkg.com/cytoscape/dist/cytoscape.min.js'></script>
<style>#cy{{width:100%;height:600px;border:1px solid #ccc}}</style>
</head><body><div id='cy'></div><script>
var elems={json.dumps(elements)};
var cy=cytoscape({{container:document.getElementById('cy'),elements:elems,layout:{{name:'breadthfirst',directed:true,padding:10}},style:[{{selector:'node',style:{{'content':'data(id)','text-valign':'center','shape':'roundrectangle','background-color':'#a3d5ff','width':'label','height':'label','padding':'10px'}}}},{{selector:'edge',style:{{'curve-style':'bezier','target-arrow-shape':'triangle'}}}}]}});
</script></body></html>"""
        with open(filename, 'w') as f:
            f.write(html)
        webbrowser.open_new_tab('file://' + os.path.abspath(filename))
        return {"status": "success", "message": f"Opened {filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ───────────────────────── Inline DAG Display ───────────────────────── #
@FunctionTool
def create_inline_dag_display(dag: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Create a text-based inline visualization of the DAG for chat display.
    Returns a formatted string showing the execution order and dependencies.
    """
    try:
        if not isinstance(dag, dict):
            return {"error": f"Expected dictionary for DAG, got {type(dag).__name__}: {dag}"}
        
        if "error" in dag:
            return {"error": f"DAG build failed: {dag['error']}"}
        
        # Find services with no dependencies (root nodes)
        all_services = set(dag.keys())
        dependent_services = set()
        for deps in dag.values():
            dependent_services.update(deps)
        root_services = all_services - dependent_services
        
        # Create topological order
        ordered, seen = [], set()
        def visit(svc):
            if svc in seen:
                return
            for dep in dag.get(svc, []):
                visit(dep)
            seen.add(svc)
            ordered.append(svc)
        
        for svc in dag:
            visit(svc)
        
        # Build the visualization
        lines = []
        lines.append("🔄 **Execution Order & Dependencies:**")
        lines.append("")
        
        # Show execution order
        lines.append("📋 **Step-by-Step Execution:**")
        for i, svc in enumerate(ordered, 1):
            deps = dag.get(svc, [])
            if deps:
                deps_str = ", ".join(deps)
                lines.append(f"  {i}. **{svc}** (depends on: {deps_str})")
            else:
                lines.append(f"  {i}. **{svc}** (no dependencies)")
        lines.append("")
        
        # Show dependency graph
        lines.append("🔗 **Dependency Graph:**")
        for svc in ordered:
            deps = dag.get(svc, [])
            if deps:
                deps_str = " → ".join(deps)
                lines.append(f"  {deps_str} → **{svc}**")
            else:
                lines.append(f"  **{svc}** (starts here)")
        lines.append("")
        
        # Show summary
        lines.append("📊 **Summary:**")
        lines.append(f"  • Total services: {len(ordered)}")
        lines.append(f"  • Root services (no dependencies): {len(root_services)}")
        lines.append(f"  • Services with dependencies: {len(ordered) - len(root_services)}")
        
        return {
            "status": "success", 
            "inline_dag": "\n".join(lines),
            "execution_order": ordered,
            "root_services": list(root_services)
        }
        
    except Exception as e:
        return {"error": f"Failed to create inline DAG display: {str(e)}"}

# 1. Skeleton: parse_user_goal
@FunctionTool
def parse_user_goal(prompt: str) -> Dict[str, Any]:
    """
    Run LLM over the raw user prompt → return a short intent blob:
      { goal: str, hints: List[str] }
    Cleans code fences from LLM output before JSON parsing.
    """
    system_msg = (
        "You are an assistant that extracts the high-level goal and explicit service hints from a GCP infrastructure request. "
        "Focus on identifying which of these 20 GCP services are mentioned or implied:\n"
        "1. Compute Engine\n"
        "2. BigQuery\n"
        "3. Pub/Sub\n"
        "4. Dataflow\n"
        "5. IAM\n"
        "6. Cloud Run\n"
        "7. VPC\n"
        "8. Dataproc\n"
        "9. Firestore\n"
        "10. Cloud Storage\n"
        "11. Cloud SQL\n"
        "12. Cloud Logging\n"
        "13. Cloud Build\n"
        "14. Artifact Registry\n"
        "15. Vertex AI\n"
        "16. GKE Autopilot\n"
        "17. Cloud Monitoring\n"
        "18. Cloud Deploy\n"
        "19. Secret Manager\n"
        "20. Cloud Functions\n\n"
        "Return JSON with keys:\n"
        "- goal (string): A clear, concise description of what the user wants to achieve\n"
        "- hints (list of strings): List of GCP service names that are explicitly mentioned or clearly implied\n\n"
        "Example:\n"
        "Input: 'Set up a real-time analytics pipeline: ingest events from Pub/Sub, process them in Dataflow, store results in BigQuery, deploy a visualization API on Cloud Run, and then set up an alert when error rate exceeds 1%.'\n"
        "Output: {\"goal\": \"Set up a real-time analytics pipeline with event ingestion, processing, storage, visualization, and monitoring\", \"hints\": [\"Pub/Sub\", \"Dataflow\", \"BigQuery\", \"Cloud Run\", \"Cloud Monitoring\"]}"
    )
    full = f"SYSTEM: {system_msg}\nUSER: {prompt}"
    raw = call_llm(full)
    # Strip code fences and optional 'json' marker
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r'```$', '', cleaned)
    try:
        return json.loads(cleaned)
    except Exception as e:
        return {"error": f"Could not parse intent JSON: {e}\nRaw: {cleaned}"}

# 2. Capability catalog lookup
@FunctionTool
def lookup_capability(action: str) -> Dict[str, Any]:
    spec = CAPS.get("actions", {}).get(action)
    if not spec:
        return {"error": f"Action '{action}' not in capabilities"}
    spec_out = spec.copy()
    spec_out["needs_design"] = (spec == "TBD")
    return spec_out

# 3. High-level planning: build_service_dag
@FunctionTool
def build_service_dag(intent_blob: Dict[str, Any]) -> Dict[str, List[str]]:
    # Check if intent_blob is actually a dictionary and not an error response
    if not isinstance(intent_blob, dict):
        return {"error": f"Expected dictionary for intent_blob, got {type(intent_blob).__name__}: {intent_blob}"}
    
    # Check if this is an error response from parse_user_goal
    if "error" in intent_blob:
        return {"error": f"Intent parsing failed: {intent_blob['error']}"}
    
    services = [
        "Compute Engine", "BigQuery", "Pub/Sub", "Dataflow", "IAM", "Cloud Run", 
        "VPC", "Dataproc", "Firestore", "Cloud Storage", "Cloud SQL", "Cloud Logging", 
        "Cloud Build", "Artifact Registry", "Vertex AI", "GKE Autopilot", 
        "Cloud Monitoring", "Cloud Deploy", "Secret Manager", "Cloud Functions"
    ]
    
    prompt = (
        f"Available GCP services: {', '.join(services)}\n\n"
        f"User Goal: {intent_blob.get('goal')}\n"
        f"Identified Services: {', '.join(intent_blob.get('hints', []))}\n\n"
        "Create a Python dictionary that represents the execution order for setting up this infrastructure.\n"
        "Each service should depend on the services that must be set up BEFORE it.\n\n"
        "Rules:\n"
        "1. Services with no dependencies should have an empty list []\n"
        "2. Services that depend on other services should list those dependencies\n"
        "3. Consider logical dependencies (e.g., VPC before Compute Engine, IAM before most services)\n"
        "4. Consider data flow dependencies (e.g., Pub/Sub before Dataflow, Dataflow before BigQuery)\n"
        "5. Consider monitoring dependencies (Cloud Monitoring often depends on the services it monitors)\n\n"
        "Example:\n"
        "For 'real-time analytics pipeline: Pub/Sub → Dataflow → BigQuery → Cloud Run → Cloud Monitoring':\n"
        "{\n"
        '  "Pub/Sub": [],\n'
        '  "Dataflow": ["Pub/Sub"],\n'
        '  "BigQuery": ["Dataflow"],\n'
        '  "Cloud Run": ["BigQuery"],\n'
        '  "Cloud Monitoring": ["Cloud Run"]\n'
        "}\n\n"
        "Return ONLY the Python dictionary. Do not include any explanations or markdown formatting."
    )
    raw = call_llm(prompt)
    clean = re.sub(r"^```[a-z]*|```$", "", raw, flags=re.IGNORECASE).strip()
    try:
        dag = ast.literal_eval(clean)
        return dag if isinstance(dag, dict) else {"error": "DAG not a dict"}
    except Exception as e:
        return {"error": f"Failed parse DAG: {e}\nRaw: {raw}"}

# 4. Mid-level planning: expand_to_tool_plan
@FunctionTool
def expand_to_tool_plan(dag: Dict[str, List[str]]) -> Dict[str, Any]:
    # Check if dag is actually a dictionary and not an error response
    if not isinstance(dag, dict):
        return {"error": f"Expected dictionary for DAG, got {type(dag).__name__}: {dag}"}
    
    # Check if this is an error response from build_service_dag
    if "error" in dag:
        return {"error": f"DAG build failed: {dag['error']}"}
    
    # Service to action mapping
    service_to_actions = {
        "Compute Engine": ["compute.create_vm", "compute.delete_vm", "compute.get_external_ip", "compute.snapshot_disk"],
        "BigQuery": ["bigquery.create_dataset", "bigquery.create_table", "bigquery.insert_json", "bigquery.export_table_gcs"],
        "Pub/Sub": ["pubsub.create_topic", "pubsub.create_subscription", "pubsub.publish", "pubsub.pull"],
        "Dataflow": ["dataflow.launch_flex_template", "dataflow.monitor_job", "dataflow.cancel_job", "dataflow.list_jobs"],
        "IAM": ["iam.create_sa", "iam.grant_role", "iam.delete_sa"],
        "Cloud Run": ["cloudrun.deploy_service", "cloudrun.update_env", "cloudrun.pause_service", "cloudrun.delete_service"],
        "VPC": ["vpc.manage_vpc_network", "vpc.check_network_subnets", "vpc.add_serverless_connector"],
        "Dataproc": ["dataproc.create_cluster", "dataproc.run_pyspark", "dataproc.delete_cluster", "dataproc.submit_hivejob"],
        "Firestore": ["firestore.create_db", "firestore.set_ttl", "firestore.seed_docs", "firestore.export_gcs"],
        "Cloud Storage": ["storage.create_bucket", "storage.upload_blob", "storage.set_lifecycle_rule"],
        "Cloud SQL": ["cloudsql.create_instance", "cloudsql.import_sql", "cloudsql.set_ip", "cloudsql.delete_instance"],
        "Cloud Logging": ["logging.create_sink", "logging.list_sinks"],
        "Cloud Build": ["cloudbuild.build_docker", "cloudbuild.clone_repo_zip"],
        "Artifact Registry": ["artifactregistry.create_repo", "artifactregistry.push_image", "artifactregistry.delete_repo"],
        "Vertex AI": ["vertex.train_custom", "vertex.deploy_endpoint", "vertex.batch_predict", "vertex.delete_endpoint"],
        "GKE Autopilot": ["gke.create_cluster", "gke.helm_install", "gke.scale_deployment", "gke.delete_cluster"],
        "Cloud Monitoring": ["cloudmonitoring.create_dashboard", "cloudmonitoring.create_alert", "cloudmonitoring.delete_dashboard"],
        "Cloud Deploy": ["clouddeploy.promote_release", "clouddeploy.watch_rollout", "clouddeploy.rollback_release"],
        "Secret Manager": ["secretmanager.create_secret", "secretmanager.add_version", "secretmanager.access_secret"],
        "Cloud Functions": ["cloudfunctions.deploy", "cloudfunctions.update", "cloudfunctions.delete"]
    }
    
    plan = []
    seen = set()
    
    def visit(svc):
        if svc in seen:
            return
        for dep in dag.get(svc, []):
            visit(dep)
        seen.add(svc)
        
        # Get available actions for this service
        actions = service_to_actions.get(svc, [])
        if actions:
            # Use the first action as the primary action for this service
            primary_action = actions[0]
            # Get required parameters from capabilities
            action_spec = CAPS.get("actions", {}).get(primary_action, {})
            
            # Handle case where action_spec might be a string (like "TBD")
            if isinstance(action_spec, dict):
                req = action_spec.get("params", {}).get("required") or []
            else:
                # If action_spec is a string (like "TBD"), use empty required params
                req = []
            
            params = {p: None for p in req}
            plan.append({
                "service": svc,
                "action": primary_action,
                "params": params,
                "available_actions": actions
            })
        else:
            # Fallback for unknown services
            plan.append({
                "service": svc,
                "action": f"{svc.lower().replace(' ', '')}.setup",
                "params": {},
                "available_actions": [],
                "note": "Service not fully implemented in capabilities"
            })
    
    # Process services in dependency order
    for svc in dag:
        visit(svc)
    
    # Create inline DAG display for chat
    inline_dag_result = create_inline_dag_display(dag)
    
    # visualize the DAG in browser (optional)
    open_dag_page(dag)
    
    return {
        "tool_plan": plan,
        "execution_order": list(seen),
        "total_services": len(seen),
        "inline_dag_display": inline_dag_result.get("inline_dag", "Failed to create inline display"),
        "dag_summary": {
            "root_services": inline_dag_result.get("root_services", []),
            "execution_order": inline_dag_result.get("execution_order", [])
        }
    }

# 5. Extract selected services from the DAG
@FunctionTool
def extract_services(dag: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Given a service dependency DAG, return the ordered list of unique services.
    """
    # Check if dag is actually a dictionary and not an error response
    if not isinstance(dag, dict):
        return {"error": f"Expected dictionary for DAG, got {type(dag).__name__}: {dag}"}
    
    # Check if this is an error response from build_service_dag
    if "error" in dag:
        return {"error": f"DAG build failed: {dag['error']}"}
    
    # simple topological order: parents before children
    ordered, seen = [], set()
    def visit(s):
        if s in seen: return
        for dep in dag.get(s, []): visit(dep)
        seen.add(s)
        ordered.append(s)
    for svc in dag:
        visit(svc)
    
    return {
        "selected_services": ordered,
        "total_services": len(ordered),
        "service_dependencies": dag
    }

# 6. Map each service to its available tools
@FunctionTool
def map_services_to_tools(selected_services: List[str]) -> Dict[str, Any]:
    """
    Map each selected service to its available tools and capabilities.
    """
    # Check if selected_services is actually a list
    if not isinstance(selected_services, list):
        return {"error": f"Expected list for selected_services, got {type(selected_services).__name__}: {selected_services}"}
    
    # Service to action mapping (same as in expand_to_tool_plan)
    service_to_actions = {
        "Compute Engine": ["compute.create_vm", "compute.delete_vm", "compute.get_external_ip", "compute.snapshot_disk"],
        "BigQuery": ["bigquery.create_dataset", "bigquery.create_table", "bigquery.insert_json", "bigquery.export_table_gcs"],
        "Pub/Sub": ["pubsub.create_topic", "pubsub.create_subscription", "pubsub.publish", "pubsub.pull"],
        "Dataflow": ["dataflow.launch_flex_template", "dataflow.monitor_job", "dataflow.cancel_job", "dataflow.list_jobs"],
        "IAM": ["iam.create_sa", "iam.grant_role", "iam.delete_sa"],
        "Cloud Run": ["cloudrun.deploy_service", "cloudrun.update_env", "cloudrun.pause_service", "cloudrun.delete_service"],
        "VPC": ["vpc.manage_vpc_network", "vpc.check_network_subnets", "vpc.add_serverless_connector"],
        "Dataproc": ["dataproc.create_cluster", "dataproc.run_pyspark", "dataproc.delete_cluster", "dataproc.submit_hivejob"],
        "Firestore": ["firestore.create_db", "firestore.set_ttl", "firestore.seed_docs", "firestore.export_gcs"],
        "Cloud Storage": ["storage.create_bucket", "storage.upload_blob", "storage.set_lifecycle_rule"],
        "Cloud SQL": ["cloudsql.create_instance", "cloudsql.import_sql", "cloudsql.set_ip", "cloudsql.delete_instance"],
        "Cloud Logging": ["logging.create_sink", "logging.list_sinks"],
        "Cloud Build": ["cloudbuild.build_docker", "cloudbuild.clone_repo_zip"],
        "Artifact Registry": ["artifactregistry.create_repo", "artifactregistry.push_image", "artifactregistry.delete_repo"],
        "Vertex AI": ["vertex.train_custom", "vertex.deploy_endpoint", "vertex.batch_predict", "vertex.delete_endpoint"],
        "GKE Autopilot": ["gke.create_cluster", "gke.helm_install", "gke.scale_deployment", "gke.delete_cluster"],
        "Cloud Monitoring": ["cloudmonitoring.create_dashboard", "cloudmonitoring.create_alert", "cloudmonitoring.delete_dashboard"],
        "Cloud Deploy": ["clouddeploy.promote_release", "clouddeploy.watch_rollout", "clouddeploy.rollback_release"],
        "Secret Manager": ["secretmanager.create_secret", "secretmanager.add_version", "secretmanager.access_secret"],
        "Cloud Functions": ["cloudfunctions.deploy", "cloudfunctions.update", "cloudfunctions.delete"]
    }
    
    mapping = {}
    total_tools = 0
    
    for svc in selected_services:
        actions = service_to_actions.get(svc, [])
        tool_names = [action.split('.', 1)[1] for action in actions]
        mapping[svc] = {
            "tools": tool_names,
            "actions": actions,
            "tool_count": len(tool_names)
        }
        total_tools += len(tool_names)
    
    return {
        "tool_mapping": mapping,
        "total_services": len(selected_services),
        "total_tools": total_tools,
        "services_with_tools": [svc for svc in selected_services if mapping.get(svc, {}).get("tool_count", 0) > 0]
    }

# 7. Stub for param elicitation (phase 4)
@FunctionTool
def prompt_for_missing_params(plan: Dict[str, Any]) -> Dict[str, Any]:
    return plan

# ───────────────────────── Tool Call Visualization ───────────────────────── #
@FunctionTool
def visualize_tool_calls(tool_calls: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Create a visual representation of tool calls in execution order.
    Input: List of tool calls from build_tool_plan
    Output: Formatted string showing the execution flow
    """
    try:
        if not isinstance(tool_calls, list):
            return {"error": f"Expected list for tool_calls, got {type(tool_calls).__name__}: {tool_calls}"}
        
        if not tool_calls:
            return {"error": "No tool calls provided"}
        
        lines = []
        lines.append("🔄 **Tool Execution Flow:**")
        lines.append("")
        
        # Create step-by-step visualization
        lines.append("📋 **Execution Steps:**")
        for i, tool_call in enumerate(tool_calls, 1):
            action = tool_call.get("action", "unknown")
            params = tool_call.get("params", {})
            
            # Extract service name from action
            service = action.split('.')[0].replace('_', ' ').title()
            
            # Show key parameters (first 2-3)
            param_items = list(params.items())[:3]
            param_str = ", ".join([f"{k}={v}" for k, v in param_items])
            if len(params) > 3:
                param_str += f" (+{len(params) - 3} more)"
            
            lines.append(f"  {i}. **{service}** - {action}")
            if param_str:
                lines.append(f"     Parameters: {param_str}")
            lines.append("")
        
        # Create flow diagram
        lines.append("🔗 **Flow Diagram:**")
        for i, tool_call in enumerate(tool_calls):
            action = tool_call.get("action", "unknown")
            service = action.split('.')[0].replace('_', ' ').title()
            
            if i == 0:
                lines.append(f"  **{service}** (starts here)")
            else:
                prev_service = tool_calls[i-1].get("action", "unknown").split('.')[0].replace('_', ' ').title()
                lines.append(f"  {prev_service} → **{service}**")
        
        lines.append("")
        
        # Create dependency analysis
        lines.append("📊 **Dependency Analysis:**")
        
        # Group by service
        service_groups = {}
        for tool_call in tool_calls:
            action = tool_call.get("action", "unknown")
            service = action.split('.')[0].replace('_', ' ').title()
            if service not in service_groups:
                service_groups[service] = []
            service_groups[service].append(action)
        
        lines.append(f"  • Total tool calls: {len(tool_calls)}")
        lines.append(f"  • Unique services: {len(service_groups)}")
        lines.append("  • Services used:")
        for service, actions in service_groups.items():
            lines.append(f"    - {service}: {len(actions)} action(s)")
        
        lines.append("")
        
        # Create execution timeline
        lines.append("⏱️ **Execution Timeline:**")
        for i, tool_call in enumerate(tool_calls):
            action = tool_call.get("action", "unknown")
            service = action.split('.')[0].replace('_', ' ').title()
            lines.append(f"  Step {i+1}: {service} ({action})")
        
        return {
            "status": "success",
            "visualization": "\n".join(lines),
            "total_steps": len(tool_calls),
            "services_used": list(service_groups.keys()),
            "execution_order": [tc.get("action", "unknown") for tc in tool_calls]
        }
        
    except Exception as e:
        return {"error": f"Failed to create tool call visualization: {str(e)}"}

# ───────────────────────── Direct Tool Planning ───────────────────────── #
@FunctionTool
def build_tool_plan(prompt: str) -> Dict[str, Any]:
    """
    Direct approach: Convert user prompt to ordered list of tool calls.
    Input: free-form user request
    Output: {"tool_calls": [{"action": "...", "params": {...}}, ...]}
    """
    SYSTEM = """
You are a GCP orchestration planner. Convert user requests into ordered tool calls.
Respond ONLY with a Python list of tool-call dictionaries in execution order.

Available GCP services and their primary actions:
- Compute Engine: compute.create_vm, compute.delete_vm
- BigQuery: bigquery.create_dataset, bigquery.create_table
- Pub/Sub: pubsub.create_topic, pubsub.create_subscription
- Dataflow: dataflow.launch_flex_template, dataflow.monitor_job
- IAM: iam.create_sa, iam.grant_role
- Cloud Run: cloudrun.deploy_service, cloudrun.update_env
- VPC: vpc.manage_vpc_network, vpc.check_network_subnets
- Dataproc: dataproc.create_cluster, dataproc.run_pyspark
- Firestore: firestore.create_db, firestore.seed_docs
- Cloud Storage: storage.create_bucket, storage.upload_blob
- Cloud SQL: cloudsql.create_instance, cloudsql.import_sql
- Cloud Logging: logging.create_sink, logging.list_sinks
- Cloud Build: cloudbuild.build_docker, cloudbuild.clone_repo_zip
- Artifact Registry: artifactregistry.create_repo, artifactregistry.push_image
- Vertex AI: vertex.train_custom, vertex.deploy_endpoint
- GKE Autopilot: gke.create_cluster, gke.helm_install
- Cloud Monitoring: cloudmonitoring.create_dashboard, cloudmonitoring.create_alert
- Cloud Deploy: clouddeploy.promote_release, clouddeploy.watch_rollout
- Secret Manager: secretmanager.create_secret, secretmanager.add_version
- Cloud Functions: cloudfunctions.deploy, cloudfunctions.update

Rules:
1. Order matters - dependencies first (e.g., IAM before services, VPC before Compute Engine)
2. Use realistic parameter values or None for required fields
3. Focus on the most essential actions for the user's goal
4. Keep it simple - 3-5 tool calls max for most requests

Example:
Input: "Set up a real-time analytics pipeline: Pub/Sub → Dataflow → BigQuery"
Output:
[
  {"action": "iam.create_sa", "params": {"project_id": "my-project", "display_name": "Analytics SA"}},
  {"action": "pubsub.create_topic", "params": {"project_id": "my-project", "topic_id": "events"}},
  {"action": "dataflow.launch_flex_template", "params": {
    "project_id": "my-project", "region": "us-central1", "job_name": "stream-processor",
    "template_path": "gs://dataflow-templates/latest/PubSub_to_BigQuery",
    "parameters": {"inputTopic": "projects/my-project/topics/events", "outputTable": "my-project:analytics.events"}
  }},
  {"action": "bigquery.create_dataset", "params": {"project_id": "my-project", "dataset_id": "analytics"}},
  {"action": "bigquery.create_table", "params": {"project_id": "my-project", "dataset_id": "analytics", "table_id": "events", "schema": "event_id:STRING,timestamp:TIMESTAMP,data:STRING"}}
]
"""
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    raw = model.generate_content(f"{SYSTEM}\nUSER:\n{prompt}").text
    
    # Clean up the response
    clean = re.sub(r"^```[a-z]*|```$", "", raw, flags=re.IGNORECASE).strip()
    
    try:
        tool_calls = ast.literal_eval(clean)
        if isinstance(tool_calls, list):
            return {"tool_calls": tool_calls}
        else:
            return {"error": f"Expected list, got {type(tool_calls).__name__}"}
    except Exception as e:
        return {"error": f"Could not parse tool list: {e}\nRaw: {raw}"}


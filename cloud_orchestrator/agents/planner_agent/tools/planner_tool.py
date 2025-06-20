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

# 1. Skeleton: parse_user_goal
@FunctionTool
def parse_user_goal(prompt: str) -> Dict[str, Any]:
    """
    Run LLM over the raw user prompt → return a short intent blob:
      { goal: str, hints: List[str] }
    Cleans code fences from LLM output before JSON parsing.
    """
    system_msg = (
        "You are an assistant that extracts the high-level goal and any explicit "
        "service hints from a GCP infrastructure request. Return JSON with keys: "
        "goal (string) and hints (list of strings)."
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
    services = list({act.split('.')[0] for act in CAPS.get("actions", {})})
    prompt = (
        f"Available: {', '.join(services)}\n"
        f"Goal: {intent_blob.get('goal')}\n"
        f"Hints: {', '.join(intent_blob.get('hints', []))}\n"
        "Return ONLY a Python dict mapping service->list of dependent services."
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
    plan = []
    seen = set()
    def visit(svc):
        if svc in seen:
            return
        for dep in dag.get(svc, []):
            visit(dep)
        seen.add(svc)
        acts = [a for a in CAPS.get("actions", {}) if a.startswith(f"{svc}.")]
        act = acts[0] if acts else f"{svc}.UNKNOWN"
        req = CAPS.get("actions", {}).get(act, {}).get("params", {}).get("required") or []
        params = {p: None for p in req}
        plan.append({"action": act, "params": params})
    for s in dag:
        visit(s)
    # visualize the DAG
    open_dag_page(dag)
    return {"tool_plan": plan}

# 5. Extract selected services from the DAG
@FunctionTool
def extract_services(dag: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Given a service dependency DAG, return the ordered list of unique services.
    """
    # simple topological order: parents before children
    ordered, seen = [], set()
    def visit(s):
        if s in seen: return
        for dep in dag.get(s, []): visit(dep)
        seen.add(s)
        ordered.append(s)
    for svc in dag:
        visit(svc)
    return {"selected_services": ordered}

# 6. Map each service to its available tools
@FunctionTool
def map_services_to_tools(selected_services: List[str]) -> Dict[str, Any]:
    """
    Load capabilities.yaml and map each selected service to its list of tool names.
    """
    # CAPS is the raw YAML dict loaded at module top
    mapping = {}
    for svc in selected_services:
        key = svc.lower().replace(" ", "")  # match prefix in actions
        actions = [a for a in CAPS.get("actions", {}) if a.startswith(f"{key}.")]
        mapping[svc] = [a.split('.', 1)[1] for a in actions]
    return {"tool_mapping": mapping}

# 7. Stub for param elicitation (phase 4)
@FunctionTool
def prompt_for_missing_params(plan: Dict[str, Any]) -> Dict[str, Any]:
    return plan


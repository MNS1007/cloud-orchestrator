from google.adk.tools.function_tool import FunctionTool
from typing import Dict
import google.generativeai as genai
import ast
import re
import json
import os
import webbrowser

def open_dag_page(parsed_response: dict, filename="dag_visualization.html"):
    dag = parsed_response
    print("📦 DAG Extracted:", dag)
    # Build nodes and edges
    elements = []
    added_nodes = set()

    for source, targets in dag.items():
        if source not in added_nodes:
            elements.append({"data": {"id": source}})
            added_nodes.add(source)
        for target in targets:
            if target not in added_nodes:
                elements.append({"data": {"id": target}})
                added_nodes.add(target)
            elements.append({"data": {"source": source, "target": target}})
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>GCP DAG Visualization</title>
        <script src="https://unpkg.com/cytoscape@3.20.0/dist/cytoscape.min.js"></script>
        <style>
            #cy {{
                width: 100%;
                height: 600px;
                display: block;
                border: 1px solid #ccc;
            }}
        </style>
    </head>
    <body>
        <h2 style="text-align:center;">GCP Service DAG</h2>
        <div id="cy"></div>
        <script>
            const elements = JSON.parse(`{json.dumps(elements)}`);
            console.log("DEBUG ELEMENTS:", elements);
            var cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: elements,
                layout: {{
                    name: 'breadthfirst',
                    directed: true,
                    padding: 10
                }},
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'content': 'data(id)',
                            'text-valign': 'center',
                            'color': '#000',
                            'background-color': '#a3d5ff',
                            'shape': 'roundrectangle',
                            'text-wrap': 'wrap',
                            'text-max-width': 200,
                            'font-size': 16,
                            'padding': '20px',
                            'width': 'label',          // allows dynamic sizing
                            'height': 'label'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 2,
                            'line-color': '#999',
                            'target-arrow-color': '#999',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier'
                        }}
                    }}
                ]
            }});
        </script>
    </body>
    </html>
    """

    with open(filename, "w") as f:
        f.write(html_content)

    webbrowser.open_new_tab("file://" + os.path.abspath(filename))

GCP_SERVICES = [
    "Compute Engine", "BigQuery", "Pub/Sub", "Dataflow", "IAM",
    "Billing Budget API", "Quotas API", "Cloud Run", "VPC", "Dataproc",
    "Firestore", "Cloud Storage", "Cloud SQL", "Cloud Logging", "Cloud Build",
    "Artifact Registry", "Vertex AI", "GKE Autopilot", "Cloud Monitoring", "Cloud Deploy", "Secret Manager"
]

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def call_llm(prompt: str, model: str = "gemini-2.0-flash") -> str:
    model = genai.GenerativeModel(model)
    response = model.generate_content(prompt)
    return response.text.strip()

def parse_dag_output(output: str) -> dict:
    """
    Parses LLM output that may be wrapped in a 'python' code block and returns a dictionary.

    Args:
        output (str): LLM-generated DAG string.

    Returns:
        dict: Parsed dictionary if valid, else error message.
    """
    try:
        # Remove leading 'python' and any code fencing/backticks
        cleaned = re.sub(r'^```?python\n?', '', output.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r'```$', '', cleaned.strip())  # remove closing ``` if present

        # Try parsing the cleaned dict string safely
        parsed = ast.literal_eval(cleaned)
        if isinstance(parsed, dict):
            return parsed
        else:
            return {"error": "Parsed result is not a dictionary."}
    except Exception as e:
        return {"error": f"Failed to parse DAG output. Details: {e}"}

@FunctionTool
def build_dag_from_prompt(instruction: str) -> Dict[str, list]:
    """
    Use Gemini LLM to interpret the instruction and return a DAG of GCP service dependencies.
    """
    prompt = f"""
You are a cloud reasoning assistant.

You are given a user's cloud infrastructure request and a list of available GCP services.

Your job is to:
1. Identify which services are relevant to the task.
2. Infer dependencies between those services.
3. Return a DAG (Directed Acyclic Graph) in the form of a Python dictionary.

Each key in the dictionary should be a service, and each value should be a list of services that depend on it.

Only include services that are required. Do not invent services outside this list:

{GCP_SERVICES}

Now here is the instruction:
\"\"\"{instruction}\"\"\"

Return ONLY the Python dictionary representing the DAG. No explanations.
Do not run recursively.
"""

    try:
        response = call_llm(prompt)
        parsed_response = parse_dag_output(response)
        open_dag_page(parsed_response)
        return parsed_response
    except Exception as e:
        return {"error": f"Failed to parse DAG from Gemini response. Raw:\n{response}"}
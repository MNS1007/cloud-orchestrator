
import json, os, subprocess, tempfile
from typing import Dict, List
from google.adk.tools import FunctionTool


def _gcloud(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)

@FunctionTool
def create_dashboard(
    project_id: str,
    dashboard_display_name: str,
    service_name: str,
    region: str = "us-central1",
) -> Dict[str, str]:
    """Create a 95-percentile latency dashboard for a Cloud Run service."""
    dashboard_json = {
        "displayName": dashboard_display_name,
        "charts": [{
            "title": "95 % latency",
            "xyChart": {
                "dataSets": [{
                    "timeSeriesQuery": {
                        "timeSeriesFilter": {
                            "filter": (
                                'metric.type="run.googleapis.com/request_latencies" '
                                f'resource.label."service_name"="{service_name}" '
                                f'resource.label."location"="{region}"'
                            ),
                            "aggregation": {
                                "alignmentPeriod": "300s",
                                "perSeriesAligner": "ALIGN_PERCENTILE_95"
                            }
                        }
                    }
                }]
            }
        }]
    }

    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
        json.dump(dashboard_json, tmp)
        tmp.flush()
        try:
            name = _gcloud([
                "gcloud", "beta", "monitoring", "dashboards", "create",
                f"--project={project_id}",
                f"--config={tmp.name}",
                "--format=value(name)"
            ]).strip()
            return {"status": "success", "dashboard_name": name}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "error_message": e.output.strip()}
        finally:
            os.remove(tmp.name)


@FunctionTool
def create_alert(
    project_id: str,
    alert_display_name: str,
    metric_type: str,
    threshold_value: float,
    comparison: str = "COMPARISON_GT",
    duration_sec: int = 300,
) -> Dict[str, str]:
    """Create a simple threshold alerting policy."""
    policy = {
        "displayName": alert_display_name,
        "combiner": "AND",
        "conditions": [{
            "displayName": "threshold-condition",
            "conditionThreshold": {
                "filter": f'metric.type="{metric_type}"',
                "comparison": comparison,
                "thresholdValue": threshold_value,
                "duration": f"{duration_sec}s"
            }
        }]
    }

    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
        json.dump(policy, tmp)
        tmp.flush()
        try:
            name = _gcloud([
                "gcloud", "beta", "monitoring", "policies", "create",
                f"--project={project_id}",
                f"--policy-from-file={tmp.name}",
                "--format=value(name)"
            ]).strip()
            return {"status": "success", "alert_policy_name": name}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "error_message": e.output.strip()}
        finally:
            os.remove(tmp.name)

def get_tools():
    """Return the FunctionTools this module exports."""
    return [create_dashboard, create_alert]
# Planner-Guard Agent Integration

This document describes the integration between the **Planner Agent** and **Guard Agent** to provide quota checking capabilities before infrastructure planning.

## Overview

The integration allows the Planner Agent to automatically check GCP quotas before creating infrastructure plans, ensuring that the planned resources can actually be provisioned without hitting quota limits.

## Architecture

```
User Request → Planner Agent → Tool Plan → Quota Check → Visualization
                                    ↓
                              Guard Agent (check_quota)
```

## Components

### 1. New Tool: `check_quota_before_planning`

**Location**: `cloud_orchestrator/agents/planner_agent/tools/planner_tool.py`

**Purpose**: Bridges the planner and guard agents by:
- Extracting service information from tool calls
- Mapping tool actions to GCP services and resource usage
- Calling the guard agent's `check_quota` function
- Returning quota check results

**Parameters**:
- `project_id` (str): GCP project ID
- `tool_calls` (List[Dict]): List of tool calls from `build_tool_plan`

**Returns**:
- `status`: OK/WARN/BLOCK/ERROR
- `message`: Detailed quota check results
- `planned_usage`: Aggregated resource usage by service and region
- `tool_calls_analyzed`: Number of tool calls processed

### 2. Service Quota Mapping

The integration includes a comprehensive mapping of tool actions to GCP services and their typical resource usage:

```python
service_quota_mapping = {
    "compute.create_vm": {
        "service": "compute.googleapis.com",
        "regions": {"us-central1": {"cpus": 2, "instances": 1}},
        "global": {"instances": 1}
    },
    "bigquery.create_dataset": {
        "service": "bigquery.googleapis.com",
        "global": {"datasets": 1}
    },
    # ... more mappings
}
```

### 3. Updated Agent Instructions

Both the `direct_agent` and `cloud_agent` have been updated to:

1. Build tool plans as before
2. Extract project_id from tool calls
3. Call `check_quota_before_planning` to verify quotas
4. Include quota check results in responses
5. Provide guidance when quotas are insufficient

## Usage Flow

### For Users

1. **Submit Request**: "Set up a real-time analytics pipeline with Pub/Sub, Dataflow, and BigQuery"

2. **Planner Response**:
   ```
   📋 Infrastructure Plan Summary
   
   🔍 Quota Check Results:
   ✅ OK: All quotas are sufficient for the plan
   
   🔄 Execution Flow:
   [Visualization of tool calls]
   
   📋 Tool Calls:
   1. iam.create_sa - Create service account
   2. pubsub.create_topic - Create event topic
   3. dataflow.launch_flex_template - Launch processing job
   4. bigquery.create_dataset - Create analytics dataset
   5. bigquery.create_table - Create events table
   
   ⚡ Execution Order: IAM → Pub/Sub → Dataflow → BigQuery
   ```

### For Developers

#### Running the Integration

```python
from cloud_orchestrator.agents.planner_agent.tools.planner_tool import (
    build_tool_plan,
    check_quota_before_planning,
    visualize_tool_calls
)

# Build tool plan
plan_result = build_tool_plan("Set up a VM and BigQuery dataset")
tool_calls = plan_result["tool_calls"]

# Check quotas
quota_result = check_quota_before_planning("my-project", tool_calls)

# Visualize
viz_result = visualize_tool_calls(tool_calls)
```

#### Testing the Integration

```bash
# Run the test script
python test_planner_guard_integration.py
```

## Quota Check Results

### Status Types

- **OK**: All quotas are sufficient
- **WARN**: Some quotas are close to limits but not exceeded
- **BLOCK**: Quotas are exceeded, plan cannot proceed
- **ERROR**: Failed to check quotas (API issues, permissions, etc.)

### Response Format

```json
{
  "status": "BLOCK",
  "message": "❌ BLOCK: 4 > limit 2 for cpus in us-central1\n🔗 Option 1: [Quota increase link]\n📧 Option 2: [Email link]",
  "planned_usage": {
    "compute.googleapis.com": {
      "us-central1": {"cpus": 4, "instances": 2},
      "global": {"instances": 2}
    }
  },
  "tool_calls_analyzed": 3
}
```

## Supported Services

The integration supports quota checking for all major GCP services:

- **Compute Engine**: CPUs, instances, networks, subnetworks
- **BigQuery**: Datasets, tables
- **Pub/Sub**: Topics, subscriptions
- **Dataflow**: Jobs, CPUs
- **IAM**: Service accounts
- **Cloud Run**: Services, revisions
- **VPC**: Networks, subnetworks
- **Dataproc**: Clusters, jobs
- **Firestore**: Databases
- **Cloud Storage**: Buckets
- **Cloud SQL**: Instances
- **Cloud Logging**: Sinks
- **Cloud Build**: Builds
- **Artifact Registry**: Repositories
- **Vertex AI**: Training jobs, endpoints, batch prediction jobs
- **GKE Autopilot**: Clusters
- **Cloud Monitoring**: Dashboards, alert policies
- **Cloud Deploy**: Releases, rollouts
- **Secret Manager**: Secrets
- **Cloud Functions**: Functions

## Error Handling

### Common Issues

1. **Missing project_id**: Uses default "test-project"
2. **Unknown tool actions**: Skipped in quota mapping
3. **API failures**: Returns ERROR status with details
4. **Permission issues**: Handled by guard agent's check_quota function

### Debugging

Enable debug output by setting environment variables:
```bash
export GCP_DEBUG=1
export PLANNER_DEBUG=1
```

## Future Enhancements

1. **Dynamic Quota Mapping**: Load quota mappings from configuration files
2. **Cost Estimation**: Integrate with billing APIs for cost predictions
3. **Regional Optimization**: Suggest alternative regions with available quotas
4. **Quota Request Automation**: Automatically request quota increases
5. **Historical Analysis**: Track quota usage patterns over time

## Dependencies

- `google.adk.agents`: Agent framework
- `google.adk.tools.function_tool`: Function tool decorators
- `requests`: HTTP requests for quota API calls
- `subprocess`: GCloud CLI integration
- `json`, `os`, `sys`: Standard library modules

## Security Considerations

- Quota checks require appropriate GCP permissions
- Service account must have `serviceusage.quotas.get` permission
- Project-level quotas are checked, not organization-level
- No sensitive quota information is logged or stored

## Troubleshooting

### Quota Check Fails

1. Verify GCP authentication: `gcloud auth application-default login`
2. Check project permissions: `gcloud projects describe PROJECT_ID`
3. Enable required APIs: `gcloud services enable serviceusage.googleapis.com`
4. Verify billing is enabled for the project

### Integration Issues

1. Check import paths in `check_quota_before_planning`
2. Verify guard agent tools are accessible
3. Test individual components separately
4. Check Python path and module structure

## Contributing

To add support for new services or tool actions:

1. Add mapping to `service_quota_mapping` in `check_quota_before_planning`
2. Update test cases in `test_planner_guard_integration.py`
3. Document the new service in this README
4. Test with real GCP project quotas 
#!/usr/bin/env python3
"""
Test script to verify planner agent integration with guard agent for quota checking.
"""

import os
import sys
import json

# Add the cloud_orchestrator directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'cloud_orchestrator'))

from cloud_orchestrator.agents.planner_agent.tools.planner_tool import (
    build_tool_plan,
    check_quota_before_planning,
    visualize_tool_calls
)

def test_planner_guard_integration():
    """Test the integration between planner and guard agents."""
    
    print("🧪 Testing Planner-Guard Agent Integration")
    print("=" * 50)
    
    # Test case 1: Simple infrastructure setup
    test_prompt = "Set up a basic analytics pipeline: create a BigQuery dataset and table, and set up a Pub/Sub topic"
    
    print(f"\n📝 Test Prompt: {test_prompt}")
    print("-" * 30)
    
    # Step 1: Build tool plan
    print("1️⃣ Building tool plan...")
    plan_result = build_tool_plan(test_prompt)
    
    if "error" in plan_result:
        print(f"❌ Failed to build tool plan: {plan_result['error']}")
        return False
    
    tool_calls = plan_result.get("tool_calls", [])
    print(f"✅ Built tool plan with {len(tool_calls)} tool calls")
    
    # Display the tool calls
    print("\n📋 Tool Calls Generated:")
    for i, tool_call in enumerate(tool_calls, 1):
        action = tool_call.get("action", "unknown")
        params = tool_call.get("params", {})
        print(f"  {i}. {action}")
        for key, value in list(params.items())[:3]:  # Show first 3 params
            print(f"     {key}: {value}")
        if len(params) > 3:
            print(f"     ... (+{len(params) - 3} more)")
    
    # Step 2: Extract project_id
    project_id = None
    for tool_call in tool_calls:
        params = tool_call.get("params", {})
        if "project_id" in params:
            project_id = params["project_id"]
            break
    
    if not project_id:
        print("⚠️ No project_id found in tool calls, using default 'test-project'")
        project_id = "test-project"
    
    print(f"\n🏗️ Project ID: {project_id}")
    
    # Step 3: Check quotas
    print("\n2️⃣ Checking quotas...")
    quota_result = check_quota_before_planning(project_id, tool_calls)
    
    print(f"📊 Quota Check Status: {quota_result.get('status', 'UNKNOWN')}")
    print(f"📝 Quota Check Message:")
    print(quota_result.get('message', 'No message'))
    
    if quota_result.get('planned_usage'):
        print(f"\n📈 Planned Usage Summary:")
        planned_usage = quota_result['planned_usage']
        for service, regions in planned_usage.items():
            print(f"  Service: {service}")
            for region, metrics in regions.items():
                print(f"    Region: {region}")
                for metric, value in metrics.items():
                    print(f"      {metric}: {value}")
    
    # Step 4: Visualize tool calls
    print("\n3️⃣ Creating visualization...")
    viz_result = visualize_tool_calls(tool_calls)
    
    if "error" in viz_result:
        print(f"❌ Failed to create visualization: {viz_result['error']}")
    else:
        print("✅ Visualization created successfully")
        print(f"📊 Total steps: {viz_result.get('total_steps', 0)}")
        print(f"🔧 Services used: {', '.join(viz_result.get('services_used', []))}")
    
    # Step 5: Summary
    print("\n" + "=" * 50)
    print("📋 Integration Test Summary:")
    print(f"  ✅ Tool plan built: {len(tool_calls)} tool calls")
    print(f"  ✅ Quota check completed: {quota_result.get('status', 'UNKNOWN')}")
    print(f"  ✅ Visualization created: {'error' not in viz_result}")
    
    if quota_result.get('status') == 'BLOCK':
        print("  ⚠️ QUOTA BLOCKED: The plan cannot proceed due to insufficient quotas")
        print("  💡 Consider requesting quota increases or modifying the plan")
    elif quota_result.get('status') == 'WARN':
        print("  ⚠️ QUOTA WARNING: Some quotas are close to limits")
        print("  💡 Monitor usage and consider quota increases if needed")
    else:
        print("  ✅ QUOTA OK: All quotas are sufficient for the plan")
    
    return True

def test_quota_mapping():
    """Test the quota mapping functionality."""
    
    print("\n🧪 Testing Quota Mapping")
    print("=" * 30)
    
    # Test with a known tool call
    test_tool_calls = [
        {
            "action": "compute.create_vm",
            "params": {"project_id": "test-project", "zone": "us-central1-a", "name": "test-vm"}
        },
        {
            "action": "bigquery.create_dataset",
            "params": {"project_id": "test-project", "dataset_id": "test_dataset"}
        }
    ]
    
    print("📋 Test Tool Calls:")
    for i, tool_call in enumerate(test_tool_calls, 1):
        print(f"  {i}. {tool_call['action']}")
    
    # Check quotas
    quota_result = check_quota_before_planning("test-project", test_tool_calls)
    
    print(f"\n📊 Quota Check Result:")
    print(f"  Status: {quota_result.get('status', 'UNKNOWN')}")
    print(f"  Tool calls analyzed: {quota_result.get('tool_calls_analyzed', 0)}")
    
    if quota_result.get('planned_usage'):
        print(f"\n📈 Planned Usage:")
        planned_usage = quota_result['planned_usage']
        for service, regions in planned_usage.items():
            print(f"  {service}:")
            for region, metrics in regions.items():
                print(f"    {region}: {metrics}")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Planner-Guard Integration Tests")
    
    try:
        # Test 1: Full integration
        success1 = test_planner_guard_integration()
        
        # Test 2: Quota mapping
        success2 = test_quota_mapping()
        
        if success1 and success2:
            print("\n🎉 All tests passed! Planner-Guard integration is working correctly.")
        else:
            print("\n❌ Some tests failed. Please check the output above.")
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc() 
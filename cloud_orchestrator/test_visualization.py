#!/usr/bin/env python3
"""
Test script to verify the open_dag_page function works with tool calls.
"""

import os
import sys

# Add the cloud_orchestrator directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'cloud_orchestrator'))

from cloud_orchestrator.agents.planner_agent.tools.planner_tool import open_dag_page

def test_visualization():
    """Test the open_dag_page function with sample tool calls."""
    
    print("🧪 Testing Visualization Function")
    print("=" * 40)
    
    # Sample tool calls
    sample_tool_calls = [
        {
            "action": "iam.create_sa",
            "params": {"project_id": "test-project", "display_name": "Analytics SA"}
        },
        {
            "action": "pubsub.create_topic",
            "params": {"project_id": "test-project", "topic_id": "events"}
        },
        {
            "action": "dataflow.launch_flex_template",
            "params": {
                "project_id": "test-project",
                "region": "us-central1",
                "job_name": "stream-processor"
            }
        },
        {
            "action": "bigquery.create_dataset",
            "params": {"project_id": "test-project", "dataset_id": "analytics"}
        },
        {
            "action": "bigquery.create_table",
            "params": {
                "project_id": "test-project",
                "dataset_id": "analytics",
                "table_id": "events"
            }
        }
    ]
    
    print(f"📋 Testing with {len(sample_tool_calls)} tool calls:")
    for i, tool_call in enumerate(sample_tool_calls, 1):
        action = tool_call.get("action", "unknown")
        service = action.split('.')[0].replace('_', ' ').title()
        print(f"  {i}. {service} - {action}")
    
    print("\n🔄 Creating visualization...")
    
    # Test the function
    result = open_dag_page(sample_tool_calls, "test_visualization.html")
    
    print(f"\n📊 Result:")
    print(f"  Status: {result.get('status', 'unknown')}")
    print(f"  Message: {result.get('message', 'No message')}")
    
    if result.get('status') == 'success':
        print("✅ Visualization created and opened successfully!")
    elif result.get('status') == 'warning':
        print("⚠️ Visualization created but browser couldn't be opened automatically.")
        print("   Check the file path in the message above.")
    else:
        print("❌ Failed to create visualization.")
        print("   Check the error message above.")
    
    return result.get('status') in ['success', 'warning']

if __name__ == "__main__":
    print("🚀 Starting Visualization Test")
    
    try:
        success = test_visualization()
        
        if success:
            print("\n🎉 Test completed successfully!")
        else:
            print("\n❌ Test failed. Please check the output above.")
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc() 
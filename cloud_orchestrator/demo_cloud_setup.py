#!/usr/bin/env python3
"""
Demo script for Cloud Orchestrator - Cloud Setup Flow

This script demonstrates the complete flow:
1. Authentication check
2. Project listing and selection
3. Project setup
4. Infrastructure planning

Usage:
    python demo_cloud_setup.py
"""

import os
import sys
from pathlib import Path

# Add the cloud_orchestrator directory to the path
sys.path.append(str(Path(__file__).parent / "cloud_orchestrator"))

from cloud_orchestrator.agents.planner_agent.tools.planner_tool import (
    setup_cloud_environment,
    check_gcloud_auth,
    list_gcp_projects,
    create_gcp_project,
    set_active_project,
    build_tool_plan,
    open_dag_page,
)

def demo_cloud_setup():
    """Demo the complete cloud setup flow"""
    
    print("🚀 **Cloud Orchestrator Demo - Setup Flow**")
    print("=" * 50)
    
    # Step 1: Check authentication
    print("\n1️⃣ **Checking Authentication...**")
    auth_result = check_gcloud_auth()
    print(f"Status: {auth_result['status']}")
    print(f"Message: {auth_result['message']}")
    
    if not auth_result.get('authenticated', False):
        print("\n❌ **Authentication Required**")
        print("Please run: gcloud auth login")
        print("Then run this demo again.")
        return
    
    # Step 2: List projects
    print("\n2️⃣ **Listing GCP Projects...**")
    projects_result = list_gcp_projects()
    print(f"Status: {projects_result['status']}")
    print(f"Message: {projects_result['message']}")
    
    if projects_result['status'] != 'success':
        print("❌ Failed to list projects")
        return
    
    projects = projects_result.get('projects', [])
    if not projects:
        print("\n📋 **No Projects Found**")
        print("Creating a new demo project...")
        
        # Create a demo project
        demo_project_id = f"demo-project-{os.getpid()}"
        create_result = create_gcp_project(demo_project_id, "Demo Project")
        print(f"Create Result: {create_result['message']}")
        
        if create_result['status'] == 'success':
            project_id = demo_project_id
        else:
            print("❌ Failed to create project")
            return
    else:
        print(f"\n📋 **Found {len(projects)} Projects:**")
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project['name']} ({project['project_id']})")
        
        # Use the first project for demo
        project_id = projects[0]['project_id']
        print(f"\n✅ **Using Project:** {project_id}")
    
    # Step 3: Set active project
    print(f"\n3️⃣ **Setting Active Project: {project_id}**")
    set_result = set_active_project(project_id)
    print(f"Status: {set_result['status']}")
    print(f"Message: {set_result['message']}")
    
    # Step 4: Demo infrastructure planning
    print(f"\n4️⃣ **Demo Infrastructure Planning**")
    demo_request = "Set up a simple data pipeline: create a BigQuery dataset, create a Pub/Sub topic, and deploy a Cloud Function"
    
    print(f"Request: {demo_request}")
    plan_result = build_tool_plan(demo_request)
    
    if 'error' in plan_result:
        print(f"❌ Planning Error: {plan_result['error']}")
        return
    
    tool_calls = plan_result.get('tool_calls', [])
    print(f"\n✅ **Generated {len(tool_calls)} Tool Calls:**")
    
    for i, tool_call in enumerate(tool_calls, 1):
        action = tool_call.get('action', 'unknown')
        params = tool_call.get('params', {})
        print(f"  {i}. {action}")
        for key, value in params.items():
            print(f"     {key}: {value}")
    
    # Step 5: Create visualization
    print(f"\n5️⃣ **Creating Visualization...**")
    viz_result = open_dag_page(tool_calls, "demo_execution_flow.html")
    print(f"Status: {viz_result['status']}")
    print(f"Message: {viz_result['message']}")
    
    print("\n🎉 **Demo Complete!**")
    print("=" * 50)
    print("✅ Authentication: Working")
    print("✅ Project Setup: Complete")
    print("✅ Infrastructure Planning: Generated")
    print("✅ Visualization: Created")
    print(f"📁 Project ID: {project_id}")
    print("🌐 Check the generated HTML file for the execution flow visualization!")

if __name__ == "__main__":
    demo_cloud_setup() 
from google.adk.agents import Agent
from .tools.planner_tool import (
    open_dag_page,
    parse_user_goal,
    build_service_dag,
    expand_to_tool_plan,
    create_inline_dag_display,
    build_tool_plan,
    visualize_tool_calls,
    check_quota_before_planning,
    setup_cloud_environment,
    check_gcloud_auth,
    list_gcp_projects,
    create_gcp_project,
    set_active_project,
)

direct_agent = Agent(
    name="direct_planner_v1",
    model="gemini-2.5-flash",
    description="Direct GCP Planner - prompt → tool calls (simplified for hackathon/demo)",
    instruction=(
        "You are a simplified GCP infrastructure planner for hackathon/demo use.\n\n"
        "**Complete Flow:**\n"
        "1. **Setup Check**: If user mentions 'cloud setup' or similar, call setup_cloud_environment() first\n"
        "2. **Authentication**: Call check_gcloud_auth() to verify authentication status\n"
        "3. **Project Discovery**: If authenticated, call list_gcp_projects() to show available projects\n"
        "4. **Project Selection**: Help user select existing project or create new one with create_gcp_project()\n"
        "5. **Set Active Project**: Use set_active_project() to set the selected project as active\n"
        "6. **Planning**: Once setup is complete, call build_tool_plan(prompt) to convert the user request to tool calls\n"
        "7. **Visualization**: Call open_dag_page(tool_calls, 'tool_execution_flow.html') to create visual HTML page\n"
        "8. **Response**: Return both the tool plan and mention that visualization has been opened\n\n"
        "**Response Format:**\n"
        "1. Setup status and project information\n"
        "2. Brief summary of what you're setting up\n"
        "3. Mention that a detailed visualization has been opened in the browser\n"
        "4. The ordered list of tool calls that will be executed\n"
        "5. Simple explanation of the execution order\n\n"
        "**Key Detection:**\n"
        "- 'cloud setup', 'gcp setup', 'google cloud setup' → Start with setup_cloud_environment()\n"
        "- Infrastructure requests → Proceed directly to build_tool_plan()\n\n"
        "Keep it simple and direct - no complex DAGs or multi-step planning."
    ),
    tools=[
        setup_cloud_environment,
        check_gcloud_auth,
        list_gcp_projects,
        create_gcp_project,
        set_active_project,
        build_tool_plan, 
        open_dag_page,
    ],
)

cloud_agent = Agent(
    name="planner_agent_v1",
    model="gemini-2.5-flash",
    description="GCP Planner – intent→service DAG→tool plan (phase 1‑3 completed)",
    instruction=(
        "You are a GCP infrastructure planning orchestrator. Your job is to create a detailed execution plan for cloud infrastructure setup.\n\n"
        "Steps:\n"
        "1. Call parse_user_goal(prompt) to extract the goal and identify required GCP services.\n"
        "2. Feed its output into build_service_dag() to create the execution order DAG.\n"
        "3. Feed that DAG into expand_to_tool_plan() to generate the detailed tool plan.\n"
        # "4. Extract project_id from the tool plan and call check_quota_before_planning(project_id, tool_calls) to verify quotas.\n"
        # "5. If quota check returns BLOCK or WARN, include the quota check results in your response.\n"
        "4. Use open_dag_page() to visualize the DAG for the user.\n"
        "5. Return a comprehensive summary including the tool plan and execution order.\n\n"
        "If any step returns an error key, stop and return the error message.\n\n"
        "**Important Response Format:**\n"
        "After completing the plan, provide a user-friendly response that includes:\n"
        "1. A brief summary of what you're setting up\n"
        # "2. Quota check results (if any issues found)\n"
        "2. The inline DAG display (from expand_to_tool_plan output)\n"
        "3. A brief explanation of the execution order\n"
        "4. Mention that a detailed visualization has been opened in the browser\n\n"
        # "**Important:** Always check quotas before proceeding with the plan. If quotas are insufficient, clearly explain the issues and provide guidance on how to resolve them.\n\n"
        "Make the response conversational and easy to understand for the user."
    ),
    tools=[
        parse_user_goal,
        build_service_dag,
        expand_to_tool_plan,
        # check_quota_before_planning,
        open_dag_page,
        create_inline_dag_display,
    ],
)

root_agent = Agent(
    name="parent_agent",
    model="gemini-2.5-flash",
    global_instruction="You are a helpful AI assistant that can handle both general questions and Google Cloud Platform (GCP) infrastructure tasks. Be friendly, professional, and always try to be helpful.",
    instruction="""You are a versatile AI assistant with two main capabilities:

1. **General Assistance**: For questions about programming, technology, general knowledge, or any non-cloud topics, provide helpful and accurate responses directly.

2. **Cloud Infrastructure & Setup**: For Google Cloud Platform (GCP) related requests, delegate to the direct_agent sub-agent.

**When to use direct_agent:**
- User mentions GCP, Google Cloud, or specific cloud services (Compute Engine, BigQuery, Cloud Storage, etc.)
- User wants to deploy, create, or manage cloud infrastructure
- User asks about cloud architecture, scaling, or cloud operations
- User mentions Kubernetes, containers, serverless, or cloud-native concepts
- User wants to set up monitoring, logging, or security in the cloud
- **NEW**: User mentions 'cloud setup', 'gcp setup', 'google cloud setup', or needs authentication help
- **NEW**: User needs help with gcloud authentication or project selection

**When to respond directly:**
- General programming questions
- Technology explanations
- Non-cloud related questions
- General knowledge queries
- Code reviews or debugging help (non-cloud specific)

**Response Guidelines:**
- Always be polite and helpful
- For cloud requests, briefly explain that you're routing to the cloud specialist
- For general requests, provide comprehensive and accurate answers
- If unsure whether something is cloud-related, ask for clarification
- Always maintain a conversational and friendly tone

**Example responses:**
- Cloud setup request: "I'll help you set up Google Cloud! Let me route this to our cloud specialist who can guide you through authentication and project setup."
- Cloud infrastructure request: "I'll help you with that GCP infrastructure task. Let me route this to our cloud specialist who can create a detailed plan for you."
- General request: "I'd be happy to help you with that! [provide direct answer]"

Remember: Your goal is to provide the best possible assistance, whether that's direct help or smart routing to specialized agents.""",
    sub_agents=[direct_agent],  
    tools=[],
)

print(f"✅ Planner Agent '{root_agent.name}' initialized")

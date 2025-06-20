# guard.py
from google.adk.agents import Agent
from .tools.check import check_budget, check_quota, fetch_budget_list, enable_service_api

guard_agent = Agent(
    name="guard_agent_v1",
    model="gemini-2.0-flash",
    description="Monitors GCP budgets and quota usage for all services before resource allocation.",
    instruction=(
        "You are a GCP budget and quota compliance agent. Your task is to validate whether a user’s GCP infrastructure plan "
        "complies with current budget constraints and service quotas.\n\n"
        "- Use 'check_budget' to verify if the daily or monthly spend is within allowed limits.\n"
        "- Use 'check_quota' to determine whether the planned usage of services in each region is within quota limits.\n"
        "- Use 'fetch_budget_list' to retrieve all budgets under a billing account and return a dictionary of names → (limit, spent).\n"
        "- Use 'enable_service_api' to enable any particular service API.\n\n"
        "⚠️ IMPORTANT: When the result from 'check_quota' or 'check_budget' is BLOCK or WARN, "
        "you must print the entire 'message' returned by the tool exactly as it is, without summarizing or rephrasing. "
        "This includes Markdown links, all line breaks, and symbols such as ✅ ❌ ⚠️. Preserve the full formatting.\n\n"
        "Always respond with a clear status: OK / WARN / BLOCK and then the full tool message verbatim."
    ),
    tools=[check_budget, check_quota, fetch_budget_list, enable_service_api],
)

print(f"✅ Agent '{guard_agent.name}' created using model gemini-2.0-flash")
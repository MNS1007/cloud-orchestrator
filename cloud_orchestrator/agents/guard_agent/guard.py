from google.adk.agents import Agent
from google.adk.tools import tool

class GuardAgent(Agent):
    @tool(name="check_budget")
    def check_budget(self, project_id: str, dollars: float) -> dict:
        #
        return {"budget_ok": True}

    @tool(name="check_quota")
    def check_quota(self, project_id: str, metric: str, need: int) -> dict:
        return {"quota_ok": True}
from google.adk.agents import Agent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.function_tool import FunctionTool
import yaml, pathlib, json
import os

_CAPS = yaml.safe_load(open(pathlib.Path(__file__).parents[2] / "capabilities.yaml"))

class PlannerAgent(LlmAgent):
    """Parse a plain-language prompt → list of ToolCalls."""
    def __init__(self, name: str):
        # Set environment variable for authentication to use worker.json
        creds_path = pathlib.Path(__file__).parents[3] / "creds" / "worker.json"
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)
        # Set the project ID explicitly
        os.environ["GOOGLE_CLOUD_PROJECT"] = "cloud4bp"
        print(f"Using credentials from: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
        print(f"Using project: {os.environ['GOOGLE_CLOUD_PROJECT']}")
        
        super().__init__(
            name=name,
            model="gemini-2.0-flash",  # Using gemini-pro which is more accessible
            description="An agent that plans and coordinates cloud operations",
            instruction="""You are a cloud operations planner. Your job is to:
1. Parse user requests into a sequence of cloud operations
2. Ensure operations are properly ordered and dependencies are met
3. Return a structured plan that can be executed by other agents"""
        )

    async def plan(self, message: str):
        spec = {
            "type": "object",
            "properties": {
                "steps": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "service_action": {"type": "string"},
                        "params": {"type": "object"}
                    },
                    "required": ["service_action"]
                }}
            },
            "required": ["steps"]
        }
        
        # Use the agent's built-in planning capabilities
        response = await self.llm.generate_content(
            message,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1
            }
        )
        
        # Parse the response into steps
        try:
            parsed = json.loads(response.text)
            tools = []
            for step in parsed["steps"]:
                sa = step["service_action"]              
                mod_path = _CAPS.get(sa)
                if not mod_path:
                    raise ValueError(f"{sa} not in capabilities.yaml")
                tools.append(FunctionTool(
                    name=sa.split(".")[-1],
                    description=f"Execute {sa} operation",
                    function=lambda **kwargs: None,  # Placeholder function
                    parameters=step.get("params", {})
                ))
            return tools
        except json.JSONDecodeError:
            raise ValueError("Failed to parse LLM response as JSON")
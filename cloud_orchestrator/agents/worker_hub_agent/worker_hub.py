from google.adk.agents import Agent
import importlib, inspect

class WorkerHubAgent(Agent):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            description="Worker hub agent that handles cloud operations"
        )
    
    def __getattr__(self, attr):
        if "_" not in attr:
            raise AttributeError(attr)
        service, fn = attr.split("_", 1)
        try:
            mod = importlib.import_module(f".tools.{service}", package=__package__)
            tool_fn = getattr(mod, fn)
            if not inspect.isfunction(tool_fn):
                raise AttributeError(attr)
            return tool_fn
        except (ImportError, AttributeError) as e:
            raise AttributeError(f"Tool {attr} not found: {str(e)}")
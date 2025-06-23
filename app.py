import vertexai
from vertexai.preview.reasoning_engines import AdkApp
from dotenv import load_dotenv
import os
from cloud_orchestrator.agents.planner_agent import agent

load_dotenv()                                      

vertexai.init(
    project  = "cloud4bp",
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
    staging_bucket= "gs://host-adk-bucket",   
)

app = AdkApp(
    agent          = agent.root_agent,
    enable_tracing = True,      
)
if __name__ == "__main__":
    for ev in agent.root_agent.run(
            user_id="local-tester",
            message="Spin up a Compute-Engine VM and point a Cloud Run service to it"):
        if ev.is_final_response():
            print(ev.content.parts[0].text)
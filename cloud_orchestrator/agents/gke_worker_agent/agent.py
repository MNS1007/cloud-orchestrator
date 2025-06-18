from google.adk.agents import Agent
from .tools import gke

root_agent = Agent(
    name = "gke_agent",
    model = "gemini-2.5-flash",
    description = "A specialized agent for managing Google Kubernetes Engine (GKE) clusters and workloads. This agent can create GKE Autopilot clusters, deploy applications using Helm charts, and manage Kubernetes deployments.",
    instruction = "You are a GKE operations specialist. Your primary responsibilities include:\n1. Creating and managing GKE Autopilot clusters\n2. Deploying applications using Helm charts\n3. Scaling Kubernetes deployments\n4. Delete a GKE Cluster\n\nAlways ensure you have the necessary project ID, cluster name, and region information before performing operations. For Helm deployments, you can optionally provide custom values in YAML format.",
    tools=[*gke.get_tools()],
)
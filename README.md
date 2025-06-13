# Cloud Orchestrator

A powerful cloud operations automation platform that uses AI agents to plan and execute cloud operations

## Prerequisites

- Google Cloud SDK
- A Google Cloud project with billing enabled
- Required Google Cloud APIs enabled:
  - Vertex AI API
  - Cloud Resource Manager API
  - IAM API

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cloud-orchestrator
   cd cloud_orchestrator
   ```

2. **Set up Google Cloud credentials**
   - Place your service account key file (`worker.json`) in the `creds/` directory
   - The service account should have the following roles:
     - `roles/aiplatform.user`
     - `roles/cloudresourcemanager.projectIamAdmin`
     - `roles/iam.serviceAccountUser`



3. **Run the ADK web server**
   ```bash
   adk web agents
   ```

## Project Structure

```
cloud-orchestrator/
├── cloud_orchestrator/
│   ├── agents/                 # Agent implementations
│   │   ├── planner_agent/     # Planning agent
│   ├── tools/                 # Tool implementations
│   │   ├── gcp_tools/        # service-specific tools
│   └── capabilities.yaml      
├── creds/                     # Credentials directory
│   └── worker.json           # Service account key
└── requirements.txt          # Python dependencies
```

## Development Guide

### Adding New Agents

1. Create a new directory in `cloud_orchestrator/agents/`
2. Implement your agent class inheriting from `google.adk.agents.Agent`
3. Add your agent's capabilities to `capabilities.yaml`

Example agent structure:
```python
from google.adk.agents import Agent

class MyAgent(Agent):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            description="Your agent description",
            instruction="Your agent instructions"
        )
```

### Adding New Tools

1. Create a new tool file in the appropriate tools directory
2. Implement your tool class inheriting from `google.adk.tools.function_tool.FunctionTool`
3. Register your tool in the corresponding agent

Example tool structure:
```python
from google.adk.tools.function_tool import FunctionTool

class MyTool(FunctionTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Tool description",
            function=self.execute,
            parameters={
                "param1": {"type": "string"},
                "param2": {"type": "integer"}
            }
        )

    async def execute(self, param1: str, param2: int):
        # Tool implementation
        pass
```

### Testing Your Changes

1. Run the ADK web server:
   ```bash
   adk web agents
   ```

2. Test your agent using the web interface or API:
   ```bash
   curl -X POST http://localhost:8000/agents/your_agent/run \
     -H "Content-Type: application/json" \
     -d '{"message": "Your test message"}'
   ```

## Common Issues and Solutions

1. **Permission Denied Errors**
   - Verify your service account has the correct roles
   - Check that the project ID is set correctly (should be "cloud4bp")
   - Ensure the `worker.json` file is in the correct location

2. **Model Access Issues**
   - The project uses `gemini-2.0-flash` model
   - Ensure your project has access to Vertex AI API
   - Check that billing is enabled for your project

3. **Credential Issues**
   - Verify `worker.json` exists in the `creds/` directory
   - Check that the service account key is valid and not expired
   - Ensure the `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set correctly



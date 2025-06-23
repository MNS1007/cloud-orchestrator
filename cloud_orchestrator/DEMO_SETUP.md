# Cloud Orchestrator Demo - Setup Flow

## Overview

This demo showcases the complete Google Cloud setup flow that happens before infrastructure planning begins. The agent guides users through authentication, project selection, and then proceeds with infrastructure planning.

## Demo Flow

### 1. **Authentication Check** 🔐
- Agent checks if user is authenticated with `gcloud auth login`
- If not authenticated, provides clear instructions
- If authenticated, proceeds to project selection

### 2. **Project Discovery** 📋
- Lists all available GCP projects for the authenticated user
- Shows project names, IDs, and states
- Handles cases where no projects exist

### 3. **Project Selection** ✅
- User can choose from existing projects
- Option to create a new project
- Option to enter a specific project ID
- Sets the selected project as active

### 4. **Infrastructure Planning** 🚀
- Once setup is complete, proceeds with normal planning
- Creates tool execution plans
- Generates visualizations

## How to Use

### For Users

1. **Start with Setup Request:**
   ```
   "I need to set up cloud"
   "Help me with GCP setup"
   "I want to authenticate with Google Cloud"
   ```

2. **Follow the Agent's Guidance:**
   - Run `gcloud auth login` if prompted
   - Select or create a project
   - Confirm the setup

3. **Proceed with Infrastructure:**
   ```
   "Now I want to create a data pipeline"
   "Set up a web application"
   "Deploy a machine learning model"
   ```

### For Demo Presenters

1. **Run the Demo Script:**
   ```bash
   python demo_cloud_setup.py
   ```

2. **Show the Complete Flow:**
   - Authentication check
   - Project listing
   - Project selection
   - Infrastructure planning
   - Visualization generation

## Key Features

### ✅ **Smart Detection**
- Automatically detects setup requests
- Routes to appropriate agents
- Maintains context throughout the flow

### ✅ **User-Friendly Interface**
- Clear, step-by-step instructions
- Emoji-rich responses
- Helpful error messages

### ✅ **Robust Error Handling**
- Graceful handling of authentication issues
- Project creation fallbacks
- Clear guidance for next steps

### ✅ **Visual Feedback**
- HTML visualizations of execution plans
- Progress indicators
- Status updates

## Agent Architecture

```
Root Agent
├── Auth Agent (NEW)
│   ├── Authentication tools
│   ├── Project management tools
│   └── Setup flow coordination
├── Planner Agent
│   ├── Infrastructure planning
│   ├── DAG generation
│   └── Tool call creation
├── Guard Agent
│   ├── Budget checks
│   ├── Quota verification
│   └── Security validation
└── Worker Hub Agent
    ├── Infrastructure deployment
    ├── Service management
    └── Execution monitoring
```

## Demo Scenarios

### Scenario 1: New User Setup
1. User: "I need to set up cloud"
2. Agent: Checks authentication → Guides through login
3. Agent: Lists projects → Helps create new project
4. Agent: Sets active project → Ready for planning

### Scenario 2: Existing User
1. User: "I want to deploy a web app"
2. Agent: Checks authentication → Lists projects
3. Agent: User selects existing project
4. Agent: Proceeds with infrastructure planning

### Scenario 3: Project Creation
1. User: "Create a new project and set up monitoring"
2. Agent: Authenticates → Creates new project
3. Agent: Sets as active → Plans monitoring setup

## Technical Implementation

### New Tools Added:
- `check_gcloud_auth()` - Verify authentication status
- `list_gcp_projects()` - List available projects
- `create_gcp_project()` - Create new projects
- `set_active_project()` - Set active project
- `setup_cloud_environment()` - Complete setup flow

### Agent Updates:
- New `auth_agent` for setup handling
- Updated `root_agent` routing logic
- Enhanced `direct_agent` with setup capabilities

### Error Handling:
- Graceful fallbacks for missing tools
- Clear user guidance for issues
- Robust path resolution for Cloud Run

## Deployment Notes

### Cloud Run Compatibility:
- All file paths work in containerized environment
- Authentication uses Application Default Credentials
- Browser operations disabled in serverless environment

### Local Development:
- Full browser integration for visualizations
- Direct gcloud CLI integration
- Interactive project selection

## Next Steps

1. **Test the Demo:**
   ```bash
   python demo_cloud_setup.py
   ```

2. **Deploy to Cloud Run:**
   ```bash
   adk deploy cloud_run \
   --project=$GOOGLE_CLOUD_PROJECT \
   --region=$GOOGLE_CLOUD_LOCATION \
   --service_name=$SERVICE_NAME \
   --app_name=$APP_NAME \
   --with_ui
   ```

3. **Present the Flow:**
   - Show authentication process
   - Demonstrate project selection
   - Highlight infrastructure planning
   - Display visualizations

## Troubleshooting

### Common Issues:
- **gcloud not found**: Install Google Cloud SDK
- **Authentication failed**: Run `gcloud auth login`
- **No projects**: Create a new project or check permissions
- **Path errors**: Ensure proper file structure

### Debug Commands:
```bash
# Check authentication
gcloud auth list

# List projects
gcloud projects list

# Set project
gcloud config set project PROJECT_ID

# Check current config
gcloud config list
```

---

**Ready for Demo! 🚀**

The Cloud Orchestrator now provides a complete, user-friendly setup experience that guides users from initial authentication through infrastructure planning. 
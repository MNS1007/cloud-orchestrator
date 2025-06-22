# Cloud Orchestrator - Vercel Deployment Guide

This guide will help you deploy the Cloud Orchestrator project as a shareable web application on Vercel.

## 🚀 Quick Deployment

### Option 1: Deploy with Vercel CLI

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy the project**:
   ```bash
   vercel --prod
   ```

4. **Follow the prompts**:
   - Link to existing project or create new
   - Confirm deployment settings
   - Wait for deployment to complete

### Option 2: Deploy via GitHub

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Add Vercel deployment configuration"
   git push origin main
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Configure settings and deploy

## 📁 Project Structure

```
cloud-orchestrator/
├── api/
│   └── index.py          # Main Vercel serverless function
├── cloud_orchestrator/   # Your existing ADK agents
├── vercel.json          # Vercel configuration
├── requirements.txt     # Python dependencies
└── DEPLOYMENT.md       # This file
```

## 🔧 Configuration Files

### vercel.json
- Configures Python runtime for API functions
- Sets up routing for API endpoints
- Defines function timeouts

### requirements.txt
- Lists all Python dependencies
- Includes Google Cloud libraries
- Specifies exact versions for consistency

### api/index.py
- Main serverless function
- Handles HTTP requests
- Integrates with your ADK agents
- Provides web interface

## 🌐 Features

### Web Interface
- **Modern UI**: Beautiful gradient design with glassmorphism effects
- **Real-time Processing**: Live feedback during plan generation
- **Responsive Design**: Works on desktop and mobile devices
- **Interactive Elements**: Hover effects and smooth animations

### API Endpoints
- `GET /` - Main web interface
- `POST /api/process` - Process infrastructure requests

### Agent Integration
- **Planner Agent**: Generates infrastructure plans
- **Visualization**: Creates interactive HTML diagrams
- **Tool Mapping**: Maps requests to GCP services
- **Error Handling**: Comprehensive error reporting

## 🔑 Environment Variables

Set these in your Vercel project settings:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=your_service_account_key
```

## 🚀 Usage

### For Users
1. **Visit the deployed URL**
2. **Enter infrastructure request** in the text area
3. **Click "Generate Infrastructure Plan"**
4. **Review the generated plan**
5. **Check visualization if created**

### Example Requests
- "Set up a real-time data pipeline from Pub/Sub through Dataflow into BigQuery"
- "Create a web application with Cloud Run, Cloud SQL, and Cloud Storage"
- "Deploy a machine learning model with Vertex AI and monitoring"

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**:
   - Check that all dependencies are in `requirements.txt`
   - Verify Python path configuration in `api/index.py`

2. **Timeout Errors**:
   - Increase function timeout in `vercel.json`
   - Optimize agent processing time

3. **API Key Issues**:
   - Verify environment variables are set
   - Check API key permissions

4. **Module Not Found**:
   - Ensure `cloud_orchestrator` directory is included
   - Check import paths in `api/index.py`

### Debug Mode

Enable debug logging by adding to `api/index.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Monitoring

### Vercel Analytics
- View deployment status in Vercel dashboard
- Monitor function execution times
- Check error rates and logs

### Custom Logging
Add logging to track usage:
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing request: {prompt}")
```

## 🔄 Updates

### Deploy Updates
```bash
vercel --prod
```

### Rollback
```bash
vercel rollback
```

## 🌟 Customization

### UI Customization
Edit the HTML/CSS in `api/index.py` to:
- Change colors and styling
- Add new features
- Modify layout

### Agent Integration
Extend `process_with_adk()` to:
- Add more agents
- Include quota checking
- Add cost estimation

### API Enhancement
Add new endpoints for:
- Agent status checking
- Plan history
- User authentication

## 📞 Support

For issues with:
- **Vercel Deployment**: Check Vercel documentation
- **ADK Agents**: Review agent configuration
- **Google Cloud**: Verify credentials and permissions

## 🎉 Success!

Once deployed, you'll have a shareable link like:
```
https://your-project.vercel.app
```

Share this URL with others to let them use your Cloud Orchestrator! 
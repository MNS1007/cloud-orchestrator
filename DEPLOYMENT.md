# Cloud Orchestrator Deployment Guide

This guide provides multiple options to deploy your Cloud Orchestrator so it's accessible to others without running on your laptop.

## 🚀 Option 1: Google Cloud Run (Recommended)

### Prerequisites
- Google Cloud SDK installed and authenticated
- Project `cloud4bp` with billing enabled

### Quick Deployment
```bash
# Make sure you're in the project directory
cd cloud-orchestrator

# Run the deployment script
./deploy-to-cloud-run.sh
```

### Manual Deployment
```bash
# Set project
gcloud config set project cloud4bp

# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Build and deploy
gcloud builds submit --tag gcr.io/cloud4bp/cloud-orchestrator
gcloud run deploy cloud-orchestrator \
    --image gcr.io/cloud4bp/cloud-orchestrator \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2
```

**Benefits:**
- ✅ Scales automatically
- ✅ Pay only for usage
- ✅ HTTPS included
- ✅ Global CDN
- ✅ Easy updates

## 🌐 Option 2: Vercel (Serverless Functions)

### Prerequisites
- Vercel CLI installed: `npm i -g vercel`
- Vercel account

### Deployment
```bash
# Install Vercel CLI if not already installed
npm i -g vercel

# Deploy to Vercel
vercel --prod
```

**Benefits:**
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Global edge network
- ✅ Easy integration with GitHub

## ☁️ Option 3: Google App Engine

### Create app.yaml
```yaml
runtime: python311
entrypoint: gunicorn -b :$PORT cloud_orchestrator.main:app

instance_class: F2
automatic_scaling:
  target_cpu_utilization: 0.6
  min_instances: 0
  max_instances: 10

env_variables:
  GOOGLE_CLOUD_PROJECT: "cloud4bp"
```

### Deploy
```bash
gcloud app deploy
```

## 🐳 Option 4: Docker + Any Cloud

### Build and Push to Docker Hub
```bash
# Build image
docker build -t yourusername/cloud-orchestrator .

# Push to Docker Hub
docker push yourusername/cloud-orchestrator
```

### Deploy to any cloud that supports Docker:
- **DigitalOcean App Platform**
- **AWS App Runner**
- **Azure Container Instances**
- **Heroku Container Registry**

## 🔧 Option 5: Google Compute Engine (VM)

### Create VM and Deploy
```bash
# Create VM
gcloud compute instances create cloud-orchestrator \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=debian-11 \
    --image-project=debian-cloud

# SSH and deploy
gcloud compute ssh cloud-orchestrator --zone=us-central1-a
```

## 📊 Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Google Cloud Run** | 2M requests/month | $0.00002400/100ms | Production, auto-scaling |
| **Vercel** | 100GB bandwidth | $20/month | Quick deployment, static sites |
| **App Engine** | 28 instance hours | $0.05/hour | Traditional web apps |
| **Compute Engine** | None | $0.047/hour | Full control, persistent |

## 🔐 Security Considerations

### For Production Deployments:
1. **Authentication**: Add user authentication
2. **HTTPS**: All platforms above provide this
3. **Rate Limiting**: Implement API rate limiting
4. **Environment Variables**: Store secrets securely
5. **CORS**: Configure allowed origins

### Environment Variables to Set:
```bash
GOOGLE_CLOUD_PROJECT=cloud4bp
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## 🚀 Recommended Workflow

1. **Development**: Use local `adk web agents` for testing
2. **Staging**: Deploy to Cloud Run with `--no-allow-unauthenticated`
3. **Production**: Deploy to Cloud Run with proper authentication

## 📝 Quick Start Commands

```bash
# Stop local server
pkill -f "adk web"

# Deploy to Cloud Run
./deploy-to-cloud-run.sh

# Deploy to Vercel
vercel --prod

# Check deployment status
gcloud run services describe cloud-orchestrator --region=us-central1
```

## 🆘 Troubleshooting

### Common Issues:
1. **Port already in use**: Kill existing processes with `pkill -f "adk web"`
2. **Authentication errors**: Check service account permissions
3. **Memory issues**: Increase memory allocation in deployment config
4. **Timeout errors**: Increase timeout settings

### Logs:
```bash
# Cloud Run logs
gcloud logs read --service=cloud-orchestrator

# Vercel logs
vercel logs
```

Choose the option that best fits your needs and budget! 
 
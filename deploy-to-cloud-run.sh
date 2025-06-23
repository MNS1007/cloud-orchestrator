#!/bin/bash

# Cloud Orchestrator Deployment Script for Google Cloud Run
# This script builds and deploys your application to Google Cloud Run

set -e

# Configuration
PROJECT_ID="cloud4bp"
SERVICE_NAME="cloud-orchestrator"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Deploying Cloud Orchestrator to Google Cloud Run..."

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Please authenticate with gcloud first:"
    echo "   gcloud auth login"
    echo "   gcloud config set project $PROJECT_ID"
    exit 1
fi

# Set the project
echo "📋 Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and push the Docker image
echo "🏗️ Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 10 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    --set-env-vars "GOOGLE_CLOUD_LOCATION=us-central1"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment complete!"
echo "🌐 Your Cloud Orchestrator is now live at:"
echo "   $SERVICE_URL"
echo ""
echo "📋 Share this URL with others to access your application!"
echo ""
echo "🔧 To update the deployment, just run this script again." 
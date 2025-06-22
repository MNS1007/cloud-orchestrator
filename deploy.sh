#!/bin/bash

# Cloud Orchestrator - Vercel Deployment Script
echo "🚀 Cloud Orchestrator - Vercel Deployment"
echo "========================================"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if user is logged in
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please login to Vercel..."
    vercel login
fi

# Check if we're in the right directory
if [ ! -f "vercel.json" ]; then
    echo "❌ vercel.json not found. Please run this script from the project root."
    exit 1
fi

# Check if api/index.py exists
if [ ! -f "api/index.py" ]; then
    echo "❌ api/index.py not found. Please ensure the API file exists."
    exit 1
fi

echo "✅ All checks passed!"
echo "📦 Deploying to Vercel..."

# Deploy to production
vercel --prod

echo ""
echo "🎉 Deployment complete!"
echo "📱 Your Cloud Orchestrator is now live!"
echo "🔗 Share the URL with others to let them use your infrastructure planner!" 
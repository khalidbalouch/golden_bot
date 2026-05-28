#!/usr/bin/env bash
set -e
echo "🚀 Deploying Golden Bot to Production..."

# 1. Build Image
echo "📦 Building Docker image..."
docker buildx build --push -t golden-bot:prod -f deploy/docker/base.Dockerfile .

# 2. Deploy to Kubernetes (if config exists)
if [ -f deploy/k8s/app-deployment.yaml ]; then
    echo "☸️ Applying Kubernetes config..."
    kubectl apply -f deploy/k8s/app-deployment.yaml
    kubectl rollout status deployment/golden-bot-pro
fi

# 3. Verify
echo "✅ Deployment Complete."
echo "📊 Monitor at http://localhost:8080/?token=cl_bot"

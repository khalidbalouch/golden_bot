#!/usr/bin/env bash
set -e
echo "🚀 Deploying Golden Bot to Kubernetes..."
kubectl apply -f deploy/k8s/app-deployment.yaml
kubectl rollout status deployment/golden-bot-pro
echo "✅ Deployment complete. Checking pods..."
kubectl get pods -l app=golden-bot

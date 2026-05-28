#!/usr/bin/env bash
set -e
echo "☁️ Deploying Golden Bot to Cloud..."

# 1. Build & Tag
echo "📦 Building container..."
docker build -t golden-bot:prod -f deploy/docker/base.Dockerfile .

# 2. Docker Swarm Init
echo "🐋 Initializing Docker Swarm..."
docker swarm init || true
docker stack deploy -c infra/docker/docker-compose.swarm.yml golden-bot

# 3. Verify
echo "✅ Deployment Complete."
echo "📊 Monitor at http://localhost:8080/?token=cl_bot"
echo "🔍 Logs: docker service logs golden-bot_engine"

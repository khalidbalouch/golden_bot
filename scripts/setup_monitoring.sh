#!/usr/bin/env bash
set -e
echo "🚀 Setting up Golden Bot monitoring stack..."

echo "📦 Pulling Prometheus & Alertmanager..."
docker pull prom/prometheus:latest
docker pull prom/alertmanager:latest

echo "🔧 Deploying configs..."
mkdir -p ./monitoring/configs
cp deploy/monitoring/prometheus.yml ./monitoring/configs/
cp deploy/monitoring/alertmanager.yml ./monitoring/configs/

echo "✅ Starting monitoring services..."
docker run -d -p 9090:9090 \
    -v $(pwd)/monitoring/configs/prometheus.yml:/etc/prometheus/prometheus.yml \
    --name prometheus prom/prometheus

docker run -d -p 9093:9093 \
    -v $(pwd)/monitoring/configs/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
    --name alertmanager prom/alertmanager

echo "📊 Dashboards ready at http://localhost:3000 (Grafana import: monitoring/dashboard_config/)"
echo "✅ Monitoring setup complete."

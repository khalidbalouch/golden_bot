#!/usr/bin/env bash
set -e
echo "🚀 Deploying Kafka Cluster for Golden Bot..."
docker compose -f deploy/streaming/kafka/cluster-config.yaml up -d
echo "✅ Kafka ready at localhost:9092"

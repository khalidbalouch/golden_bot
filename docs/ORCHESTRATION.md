# Golden Bot — Phase 9: Production Orchestration & Distributed Infrastructure
## Core Philosophy
**Stateful, Resilient, Observable.** Production trading systems require distributed task routing, model lifecycle tracking, zero-downtime deployments, and graceful failure recovery.
## Architecture
1. `RedisTaskQueue`: Async priority queue with visibility timeout, exponential backoff retries
2. `WorkerPool`: Horizontal scaling container for feature/inference/backtest jobs
3. `ModelRegistryClient`: MLflow integration for experiment tracking, versioning, promotion
4. `HealthCheck`: K8s-ready `/health` & `/ready` probes with Redis/PostgreSQL connectivity checks
5. `GracefulShutdown`: SIGTERM/SIGINT handling, state persistence, task draining before exit
6. `Docker Compose`: Local dev stack (App + Redis + Postgres + MLflow)
7. `Kubernetes`: Deployment + Service + HPA + Resource Limits + Liveness/Readiness probes
8. `Airflow DAGs`: Scheduled drift detection, retraining, validation, promotion pipeline
## Rate Limit & Compute Compliance
- Workers scale horizontally to offload heavy feature computation & backtesting
- Main bot process remains lightweight, handles WS streams & order routing
- All inter-service communication via Redis/REST (no direct DB polling)
## Deployment Steps
1. Local: `docker compose -f deploy/docker-compose.yml up -d`
2. K8s: `bash scripts/deploy_k8s.sh`
3. Scale: `python scripts/scale_workers.py --replicas 5`
4. Airflow: Import `deploy/airflow/dags/` into your Airflow instance
## Operational Notes
- Always test graceful shutdown in staging before production
- Model promotion requires shadow validation (Phase 5) + Airflow approval
- Redis queue depth >100 triggers HPA scaling automatically
- PostgreSQL stores trade logs, audit trails, model metadata
- MLflow tracks all experiments, artifacts, and production lineage

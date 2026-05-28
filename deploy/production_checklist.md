# Golden Bot — Production Deployment Checklist
## Pre-Deployment Validation
- [ ] All unit/integration tests pass: `pytest tests/ -v --cov=90`
- [ ] Chaos experiments pass: `python scripts/run_chaos.py`
- [ ] Benchmarks meet thresholds: P95 latency <100ms, memory <1.5GB
- [ ] Security scan clean: `bandit -r .` & Trivy image scan
- [ ] Secrets externalized: No hardcoded keys in code/config
- [ ] Audit log chaining verified: `python -c "from core.security import AuditLogger; l=AuditLogger(); print(l.verify_chain())"`
## Deployment Steps
1. Tag release: `git tag -a v1.0.0 -m "Production"`
2. Build & push: `docker buildx build --push -t registry/golden-bot:v1.0.0 .`
3. Deploy K8s: `kubectl apply -f deploy/k8s/app-deployment.yaml`
4. Monitor rollout: `kubectl rollout status deployment/golden-bot-pro`
5. Smoke test: Execute 1 dry-run trade, verify dashboard & metrics
## Rollback Procedure
1. `kubectl rollout undo deployment/golden-bot-pro`
2. Verify health endpoints & alert silence
3. Document incident & update runbooks

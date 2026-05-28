# Golden Bot — Phase 10: Monitoring, Alerting & Observability
## Core Philosophy
**If you can't measure it, you can't manage it.** Institutional-grade monitoring ensures real-time visibility into trading performance, model health, system load, and risk exposure.
## Architecture
1. `MetricsExporter`: Prometheus-native counters, gauges, histograms for all bot components
2. `AlertManager`: Rule evaluation, deduplication, multi-channel routing (Slack/PagerDuty/Email)
3. `Grafana Dashboards`: Pre-built JSON configs for Trading Performance & Model Health
4. `Alertmanager`: External routing engine with inhibition, silencing, and escalation policies
5. `Prometheus`: Time-series DB for metric scraping, storage, and querying
## Setup & Deployment
1. Run: `bash scripts/setup_monitoring.sh`
2. Start bot: Metrics auto-exposed at `http://localhost:9090/metrics`
3. Import dashboards into Grafana from `monitoring/dashboard_config/`
4. Configure webhooks in `deploy/monitoring/alertmanager.yml`
## Operational Guidelines
- **Scrape Interval**: 10-15s (balance between precision & overhead)
- **Alert Deduplication**: 5-minute window to prevent notification storms
- **Retention**: Prometheus retains 30d metrics by default (adjust via `--storage.tsdb.retention.time`)
- **High Availability**: Run duplicate Prometheus instances with Thanos/Cortex for production
## Alert Routing Matrix
| Metric | Threshold | Severity | Channel |
|--------|-----------|----------|---------|
| Drawdown > 10% | CRITICAL | PagerDuty + Slack |
| Feature PSI > 0.2 | WARNING | Slack |
| Queue Depth > 100 | WARNING | Slack |
| Bot Crash / Restart | CRITICAL | PagerDuty + Email |
## Integration Notes
- Metrics auto-register on bot startup
- Alerts evaluate against live metric stream
- Grafana panels update every 5s via Prometheus queries
- All monitoring components are fully decoupled from trading logic

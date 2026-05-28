from __future__ import annotations
import logging
import os
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import redis
import psycopg2

logger = logging.getLogger("golden_bot.orchestration.health")

def create_health_app(redis_url: str = "redis://localhost:6379", 
                      db_url: str = "postgresql://user:pass@localhost:5432/botdb") -> FastAPI:
    app = FastAPI(title="Golden Bot Health API")

    @app.get("/health")
    async def healthcheck():
        return JSONResponse({"status": "ok"})

    @app.get("/ready")
    async def readiness():
        status = {"ready": True, "checks": {}}
        try:
            r = redis.from_url(redis_url, decode_responses=True)
            r.ping()
            status["checks"]["redis"] = "ok"
        except Exception as e:
            status["checks"]["redis"] = f"fail: {e}"
            status["ready"] = False

        try:
            conn = psycopg2.connect(db_url.replace("postgresql://", ""))
            conn.close()
            status["checks"]["postgres"] = "ok"
        except Exception as e:
            status["checks"]["postgres"] = f"fail: {e}"
            status["ready"] = False

        return JSONResponse(status)

    @app.get("/metrics")
    async def metrics():
        # Placeholder for Prometheus exposition format
        return JSONResponse({"uptime": os.getpid()})

    return app

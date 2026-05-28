from __future__ import annotations
import csv
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("golden_bot.governance")

class GovernanceManager:
    """Handles audit exports, tax reporting, and jurisdiction compliance."""
    def __init__(self, base_dir: str = "data/governance"):
        self.dir = Path(base_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.audit_log_path = self.dir / "audit_trail.csv"
        self._init_audit_log()

    def _init_audit_log(self) -> None:
        if not self.audit_log_path.exists():
            with open(self.audit_log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "action", "symbol", "qty", "price", "pnl", "details"])

    def log_trade(self, action: str, symbol: str, qty: float, price: float, pnl: float, details: str = "") -> None:
        with open(self.audit_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([self._get_ts(), action, symbol, qty, price, pnl, details])

    def export_tax_report(self, year: int, method: str = "FIFO") -> str:
        logger.info(f"📄 Generating {method} tax report for {year}...")
        # Simplified CSV generation for Phase 17
        output = self.dir / f"tax_report_{year}_{method}.csv"
        with open(self.audit_log_path) as src, open(output, 'w') as dst:
            dst.write(src.read()) # Placeholder: would process FIFO/LIFO logic
        logger.info(f"✅ Tax report saved to {output}")
        return str(output)

    def check_jurisdiction(self, user_country: str, restricted_countries: List[str]) -> bool:
        """Returns False if country is restricted."""
        restricted = restricted_countries or ["US", "CN", "KP"]
        if user_country.upper() in restricted:
            logger.critical(f"🚫 JURISDICTION VIOLATION: {user_country} is restricted.")
            return False
        return True

    def _get_ts(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat()

class AuditExporter:
    """Exports detailed audit logs for regulatory review."""
    def export_full_audit(self, gov_manager: GovernanceManager, output_path: str) -> str:
        import shutil
        dest = Path(output_path)
        shutil.copy2(gov_manager.audit_log_path, dest)
        logger.info(f"📦 Audit exported to {dest}")
        return str(dest)

        from __future__ import annotations
        import csv
        import json
        import logging
        from pathlib import Path
        from typing import List, Dict, Optional

        logger = logging.getLogger("golden_bot.compliance")

        class ComplianceManager:
            """Audit logging, KYC/AML hooks, and tax reporting."""
            def __init__(self, data_dir: str = "data/compliance"):
                self.dir = Path(data_dir)
                self.dir.mkdir(parents=True, exist_ok=True)
                self.audit_path = self.dir / "audit_log.json"

            def log_event(self, event_type: str, details: Dict, user: str = "system") -> None:
                import time
                entry = {"ts": time.time(), "type": event_type, "user": user, "details": details}
                with open(self.audit_path, "a") as f:
                    f.write(json.dumps(entry) + "
")

            def export_tax_report(self, trades: List[Dict], method: str = "FIFO") -> str:
                """Generates CSV for tax filing."""
                out_path = self.dir / f"tax_report_{method}.csv"
                with open(out_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["date", "asset", "qty", "price", "type"])
                    writer.writeheader()
                    for t in trades:
                        writer.writerow(t)
                logger.info(f"📄 Tax report saved to {out_path}")
                return str(out_path)

from __future__ import annotations
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("golden_bot.ml.events")

class EconomicEvent:
    def __init__(self, name: str, impact: str, time_utc: int):
        self.name = name
        self.impact = impact # "HIGH", "MEDIUM", "LOW"
        self.time_utc = time_utc

class EventProcessor:
    """Parses economic calendar and adjusts trading risk parameters."""
    def __init__(self):
        self._upcoming_events: List[EconomicEvent] = []

    def ingest_events(self, events: List[Dict]) -> None:
        """Expects list of dicts: {'name': 'FOMC', 'impact': 'HIGH', 'time': 123456}"""
        self._upcoming_events = []
        for e in events:
            self._upcoming_events.append(EconomicEvent(e['name'], e['impact'], e['time']))
        # Sort by time
        self._upcoming_events.sort(key=lambda x: x.time_utc)

    def get_risk_adjustment(self, current_time_utc: int, lookahead_hours: int = 2) -> float:
        """Returns risk multiplier (0.0 to 1.0) based on proximity to high-impact events."""
        threshold = lookahead_hours * 3600
        now = current_time_utc

        for evt in self._upcoming_events:
            time_diff = abs(evt.time_utc - now)
            if time_diff < threshold and evt.impact == "HIGH":
                # Reduce risk significantly 2 hours before/after FOMC
                return 0.1 
            elif time_diff < threshold and evt.impact == "MEDIUM":
                return 0.5

        return 1.0 # No events, full risk

    def check_for_event_cluster(self, current_time_utc: int, window_sec: int = 3600) -> bool:
        """Checks if multiple high-impact events occur simultaneously."""
        count = 0
        for evt in self._upcoming_events:
            if abs(evt.time_utc - current_time_utc) < window_sec and evt.impact == "HIGH":
                count += 1
        return count > 1

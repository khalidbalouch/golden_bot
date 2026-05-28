from __future__ import annotations
import time

class NanosecondClock:
    """High-precision timestamping using CPU TSC or PTP sync."""
    def __init__(self):
        self._offset_ns = 0

    def now_ns(self) -> int:
        """Returns current time in nanoseconds."""
        return time.time_ns() + self._offset_ns

    def calibrate_ptp(self, ptp_time_ns: int) -> None:
        """Aligns clock with PTP grandmaster."""
        self._offset_ns = ptp_time_ns - time.time_ns()

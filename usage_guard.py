"""Best-effort, process-local Gemini request limits for a Streamlit demo.

Counts actual API attempts. These limits reset on process restart and do not
replace provider billing limits, authentication or durable storage.
"""
from __future__ import annotations
from datetime import datetime, timezone
from threading import Lock
from collections import deque
import time

class DemoQuotaReached(RuntimeError):
    pass

class ApiAttemptLimiter:
    def __init__(self, daily_limit: int = 12, minute_limit: int = 8):
        self.daily_limit = daily_limit
        self.minute_limit = minute_limit
        self._day = ''
        self._daily_calls = 0
        self._minute_calls = deque()
        self._lock = Lock()

    def consume(self):
        """Reserve one real provider request or fail before sending it."""
        with self._lock:
            current_day = datetime.now(timezone.utc).date().isoformat()
            if self._day != current_day:
                self._day = current_day
                self._daily_calls = 0
            now = time.monotonic()
            while self._minute_calls and now - self._minute_calls[0] >= 60:
                self._minute_calls.popleft()
            if self._daily_calls >= self.daily_limit:
                raise DemoQuotaReached('DEMO_DAILY_LIMIT_REACHED')
            if len(self._minute_calls) >= self.minute_limit:
                raise DemoQuotaReached('DEMO_MINUTE_LIMIT_REACHED')
            self._daily_calls += 1
            self._minute_calls.append(now)

    def remaining_today(self):
        with self._lock:
            if self._day != datetime.now(timezone.utc).date().isoformat():
                return self.daily_limit
            return max(0, self.daily_limit - self._daily_calls)

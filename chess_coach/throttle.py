import threading
import time


class LoginThrottle:
    """Remembers recent failed logins in memory and says when a login must wait."""

    def __init__(self, window=15 * 60, max_per_user=8, max_per_ip=100, max_keys=5000):
        self.window = window
        self.max_per_user = max_per_user
        self.max_per_ip = max_per_ip
        self.max_keys = max_keys
        self._failed = {}
        self._lock = threading.Lock()

    def _recent(self, key, now):
        stamps = [t for t in self._failed.get(key, []) if now - t < self.window]
        if stamps:
            self._failed[key] = stamps
        else:
            self._failed.pop(key, None)
        return stamps

    def wait_seconds(self, username, ip, now=None):
        """0 if the login may go ahead, otherwise how many seconds to wait."""
        now = time.time() if now is None else now
        longest = 0.0
        with self._lock:
            for key, limit in ((f"u:{username.lower()}", self.max_per_user),
                               (f"ip:{ip}", self.max_per_ip)):
                stamps = self._recent(key, now)
                if len(stamps) >= limit:
                    # the lock lifts when the oldest failure that counts expires
                    longest = max(longest, self.window - (now - stamps[len(stamps) - limit]))
        return int(longest) + 1 if longest > 0 else 0

    def record_failure(self, username, ip, now=None):
        now = time.time() if now is None else now
        with self._lock:
            if len(self._failed) > self.max_keys:
                self._failed.clear()
            for key in (f"u:{username.lower()}", f"ip:{ip}"):
                self._failed.setdefault(key, []).append(now)

    def record_success(self, username):
        with self._lock:
            self._failed.pop(f"u:{username.lower()}", None)

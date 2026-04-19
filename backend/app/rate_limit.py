from __future__ import annotations

import time
from collections import defaultdict

WINDOW_MS = 60_000  # 1 minute
MAX_REQUESTS = 30


_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_ip: str | None) -> tuple[bool, int]:
    """Check if a client IP has exceeded the rate limit.

    Returns:
        (is_limited, retry_after_seconds)
    """
    if not client_ip:
        return False, 0

    now = time.time() * 1000  # milliseconds
    window_start = now - WINDOW_MS

    # Prune old entries.
    recent = [ts for ts in _store[client_ip] if ts > window_start]
    _store[client_ip] = recent

    if len(recent) >= MAX_REQUESTS:
        oldest = recent[0]
        retry_after_ms = max(0, WINDOW_MS - (now - oldest))
        return True, max(1, int(retry_after_ms / 1000))

    recent.append(now)
    return False, 0

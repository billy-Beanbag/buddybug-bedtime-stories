from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from threading import Lock
from time import time

from fastapi import HTTPException, Request, status

from app.config import RATE_LIMIT_ENABLED


class InMemoryRateLimiter:
    """Single-process in-memory rate limiter for sensitive endpoints."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, *, key: str, limit: int, window_seconds: int) -> None:
        now = time()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "detail": "Rate limit exceeded",
                        "error_code": "rate_limit_exceeded",
                    },
                    headers={"Retry-After": str(window_seconds)},
                )
            events.append(now)


rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None and request.client.host:
        return request.client.host
    return "unknown"


def create_rate_limit_dependency(
    *,
    limit: int,
    window_seconds: int = 60,
    scope_key: str | None = None,
) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        if not RATE_LIMIT_ENABLED:
            return
        key = f"{get_client_ip(request)}:{scope_key or request.url.path}"
        rate_limiter.check(key=key, limit=limit, window_seconds=window_seconds)

    return dependency

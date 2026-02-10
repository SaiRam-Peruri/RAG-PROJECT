"""
Simple in-memory rate limiter.
For production at scale, use Redis-backed rate limiting.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List

from fastapi import HTTPException, Request, status

from ..config import settings


class RateLimiter:
    """Token bucket rate limiter per IP."""

    def __init__(self, rpm: int | None = None):
        self.rpm = rpm or settings.rate_limit_rpm
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def check(self, request: Request) -> None:
        """Check rate limit for request. Raises 429 if exceeded."""
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60.0  # 1 minute

        # Clean old entries
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < window
        ]

        if len(self._requests[client_ip]) >= self.rpm:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({self.rpm} req/min). Try again later.",
            )

        self._requests[client_ip].append(now)


# Singleton
rate_limiter = RateLimiter()

"""Authentication, bearer authorization, and token-bucket visitor rate limiter."""

from __future__ import annotations
import os
import time
from collections import defaultdict
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)

# Token bucket rate limiting: max 10 runs per minute per client IP
RATE_LIMIT_CAPACITY = int(os.getenv("RATE_LIMIT_CAPACITY", "10"))
RATE_LIMIT_REFILL_SECONDS = float(os.getenv("RATE_LIMIT_REFILL_SECONDS", "60.0"))


class RateLimiter:
    def __init__(self, capacity: int = RATE_LIMIT_CAPACITY, refill_seconds: float = RATE_LIMIT_REFILL_SECONDS):
        self.capacity = capacity
        self.refill_seconds = refill_seconds
        self.buckets: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.refill_seconds
        timestamps = [t for t in self.buckets[client_id] if t > window_start]
        if len(timestamps) >= self.capacity:
            return False
        timestamps.append(now)
        self.buckets[client_id] = timestamps
        return True


rate_limiter = RateLimiter()


def check_rate_limit(request: Request):
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "127.0.0.1"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: maximum {RATE_LIMIT_CAPACITY} requests per minute.",
        )


def verify_admin_key(credentials: HTTPAuthorizationCredentials | None = Security(security)):
    required_key = os.getenv("ADMIN_API_KEY", "")
    if not required_key:
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            raise HTTPException(
                status_code=403,
                detail="Admin key must be configured via ADMIN_API_KEY environment variable in production.",
            )
        return True
    if not credentials or credentials.credentials != required_key:
        raise HTTPException(status_code=401, detail="Invalid or missing admin authorization token")
    return True

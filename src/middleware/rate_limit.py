from collections import defaultdict
from time import time

from fastapi import Request

from src.core.exceptions import RateLimitError


class RateLimiter:
    def __init__(self, requests: int = 5, window: int = 60) -> None:
        self.requests = requests
        self.window = window
        self.clients: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check(self, request: Request) -> None:
        client_ip = self._get_client_ip(request)
        now = time()

        self.clients[client_ip] = [
            t for t in self.clients[client_ip] if now - t < self.window
        ]

        if len(self.clients[client_ip]) >= self.requests:
            raise RateLimitError("Too many requests")

        self.clients[client_ip].append(now)

    def reset(self) -> None:
        self.clients.clear()


rate_limiter = RateLimiter()

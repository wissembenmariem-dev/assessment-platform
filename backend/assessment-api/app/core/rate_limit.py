from fastapi import Request
from slowapi import Limiter

from app.core.config import settings


def client_ip(request: Request) -> str:
    hops = settings.trusted_proxy_hops
    forwarded = request.headers.get("X-Forwarded-For", "")
    if hops > 0 and forwarded:
        chain = [part.strip() for part in forwarded.split(",") if part.strip()]
        if len(chain) >= hops:
            return chain[-hops]
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip, storage_uri=settings.rate_limit_storage_uri)

import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.routers import sessions, test, scores, auth
from app.routers import candidate_rights

_sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_sdk.init(
        dsn=_sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
        send_default_pii=False,
        integrations=[FastApiIntegration()],
    )

limiter = Limiter(key_func=get_remote_address)

if settings.is_production:
    missing = settings.validate_production_config()
    if missing:
        print(
            f"\n[ERREUR CRITIQUE] Variables d'environnement manquantes ou invalides :\n"
            + "\n".join(f"  ✗ {v}" for v in missing)
            + "\n\nDéploiement interrompu. Remplir ces valeurs dans .env avant de relancer.\n"
        )
        sys.exit(1)

app = FastAPI(
    title="Assessment API",
    description="Plateforme d'évaluation psychométrique — Acme Talent",
    version="2.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self' https://*.supabase.co;"
    )
    return response


app.include_router(auth.router,             prefix="/api/v1")
app.include_router(sessions.router,         prefix="/api/v1")
app.include_router(test.router,             prefix="/api/v1")
app.include_router(scores.router,           prefix="/api/v1")
app.include_router(candidate_rights.router, prefix="/api/v1")

try:
    from app.routers import pdf as pdf_router
    app.include_router(pdf_router.router, prefix="/api/v1")
except ImportError:
    pass


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
async def root():
    return {"message": "Acme Talent Assessment API v2", "docs": "/docs"}

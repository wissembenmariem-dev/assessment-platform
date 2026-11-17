import hmac
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from jose import jwt

from app.core.config import settings
from app.core.database import get_supabase_admin

router = APIRouter(tags=["auth"])

TOKEN_EXPIRE_HOURS = 12
ALGORITHM = "HS256"

_LOGIN_ATTEMPTS: dict[str, list[datetime]] = defaultdict(list)
_RATE_LIMIT_MAX = 5
_RATE_LIMIT_WINDOW = timedelta(minutes=15)


def _check_rate_limit(ip: str) -> None:
    now = datetime.now(timezone.utc)
    cutoff = now - _RATE_LIMIT_WINDOW
    attempts = [t for t in _LOGIN_ATTEMPTS[ip] if t > cutoff]
    _LOGIN_ATTEMPTS[ip] = attempts
    if len(attempts) >= _RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail="Trop de tentatives. Réessayez dans 15 minutes.",
            headers={"Retry-After": "900"},
        )
    _LOGIN_ATTEMPTS[ip].append(now)

supabase_admin = get_supabase_admin()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    recruiter_id: str


@router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    client_ip = client_ip.split(",")[0].strip()
    _check_rate_limit(client_ip)

    email_match = hmac.compare_digest(body.email.lower().strip(), settings.recruiter_email.lower().strip())
    password_match = bool(settings.recruiter_password) and hmac.compare_digest(body.password, settings.recruiter_password)

    if not email_match or not password_match:
        raise HTTPException(status_code=401, detail="Identifiants incorrects.")

    result = (
        supabase_admin.table("recruiters")
        .select("id")
        .eq("email", settings.recruiter_email.lower().strip())
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        raise HTTPException(
            status_code=500,
            detail="Compte recruteur introuvable — exécutez schema.sql puis scripts/setup_db.py"
        )

    recruiter_id = result.data["id"]

    payload = {
        "sub": settings.recruiter_email,
        "recruiter_id": recruiter_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    token = jwt.encode(payload, settings.app_secret_key, algorithm=ALGORITHM)

    return LoginResponse(access_token=token, recruiter_id=recruiter_id)

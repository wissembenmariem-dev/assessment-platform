import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_supabase_admin
from app.core.rate_limit import limiter

router = APIRouter(tags=["auth"])

TOKEN_EXPIRE_HOURS = 12
ALGORITHM = "HS256"

supabase_admin = get_supabase_admin()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    recruiter_id: str


@router.post("/auth/login", response_model=LoginResponse)
@limiter.limit("5/15minutes")
async def login(body: LoginRequest, request: Request):
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

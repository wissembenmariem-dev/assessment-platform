from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import settings

_bearer = HTTPBearer()


def require_recruiter(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.app_secret_key,
            algorithms=["HS256"],
        )
        recruiter_id: str | None = payload.get("recruiter_id")
        if not recruiter_id:
            raise HTTPException(status_code=401, detail="Token invalide")
        return recruiter_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

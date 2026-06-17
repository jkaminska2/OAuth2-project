import httpx
from functools import lru_cache
from typing import List, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings

bearer_scheme = HTTPBearer(auto_error=True)

class TokenData(BaseModel):
    sub: str
    email: Optional[str] = None
    name: Optional[str] = None
    groups: List[str] = []
    preferred_username: Optional[str] = None

_jwks_cache: dict | None = None

async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.authentik_jwks_url, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache

async def _decode_token(token: str) -> dict:
    jwks = await _get_jwks()
    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            issuer=settings.authentik_issuer,
            options={"verify_aud": False},
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> TokenData:
    payload = await _decode_token(credentials.credentials)
    return TokenData(
        sub=payload["sub"],
        email=payload.get("email"),
        name=payload.get("name"),
        groups=payload.get("groups", []),
        preferred_username=payload.get("preferred_username"),
    )


def require_role(role: str):
    async def _check(user: TokenData = Depends(get_current_user)) -> TokenData:
        if role not in user.groups:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required.",
            )
        return user

    return _check

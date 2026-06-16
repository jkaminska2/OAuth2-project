from fastapi import APIRouter, Depends

from app.middleware.auth import TokenData, get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(user: TokenData = Depends(get_current_user)):   # 🔒 protected
    """Return info about the currently authenticated user (from JWT claims)."""
    return {
        "sub": user.sub,
        "email": user.email,
        "name": user.name,
        "preferred_username": user.preferred_username,
        "groups": user.groups,
    }

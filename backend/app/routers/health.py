from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Public health-check endpoint – no authentication required."""
    return {"status": "ok", "service": "taskmanager-api"}

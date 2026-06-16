from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import TokenData, require_role
from app.models import Task

router = APIRouter(prefix="/admin", tags=["admin"])

# require_role("admin") checks that the JWT `groups` claim contains "admin"
_admin = require_role("admin")


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(_admin),                     # 🔒 protected + role
):
    """
    Admin-only: aggregate statistics across ALL users.
    Requires the caller to be a member of the 'admin' group in Authentik.
    """
    total_result = await db.execute(select(func.count(Task.id)))
    total = total_result.scalar()

    by_status_result = await db.execute(
        select(Task.status, func.count(Task.id)).group_by(Task.status)
    )
    by_status = {row.status: row[1] for row in by_status_result}

    by_user_result = await db.execute(
        select(Task.owner_sub, func.count(Task.id)).group_by(Task.owner_sub)
    )
    by_user = [{"sub": row.owner_sub, "task_count": row[1]} for row in by_user_result]

    return {
        "total_tasks": total,
        "by_status": by_status,
        "by_user": by_user,
    }


@router.get("/tasks")
async def list_all_tasks(
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(_admin),                     # 🔒 protected + role
):
    """Admin-only: list every task regardless of owner."""
    result = await db.execute(select(Task).order_by(Task.id.desc()))
    tasks = result.scalars().all()
    return tasks

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import TokenData, get_current_user
from app.models import Task, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    owner_sub: str

    class Config:
        from_attributes = True


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),       # 🔒 protected
):
    """Return all tasks belonging to the current user."""
    result = await db.execute(
        select(Task).where(Task.owner_sub == user.sub).order_by(Task.id.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),       # 🔒 protected
):
    """Create a new task for the current user."""
    task = Task(title=body.title, description=body.description, owner_sub=user.sub)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    body: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),       # 🔒 protected
):
    """Update a task – only the owner can modify it."""
    task = await _get_own_task(task_id, user.sub, db)
    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.status is not None:
        task.status = body.status
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: TokenData = Depends(get_current_user),       # 🔒 protected
):
    """Delete a task – only the owner can delete it."""
    task = await _get_own_task(task_id, user.sub, db)
    await db.delete(task)
    await db.commit()


# ── Helper ─────────────────────────────────────────────────────────────────────

async def _get_own_task(task_id: int, owner_sub: str, db: AsyncSession) -> Task:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.owner_sub == owner_sub)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task

"""
Automated tests for the TaskManager API.

Strategy:
- We mock `_decode_token` to bypass real Authentik JWT validation.
- We use SQLite in-memory for the DB to avoid needing a real Postgres.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock, patch

from app.main import app
from app.database import Base, get_db

# ── In-memory test DB ──────────────────────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mock_token(sub="user-123", groups=None):
    return {
        "sub": sub,
        "email": f"{sub}@test.com",
        "name": "Test User",
        "groups": groups or [],
        "preferred_username": sub,
    }


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestHealth:
    @pytest.mark.asyncio
    async def test_health_is_public(self, client):
        """GET /health should work without any token."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestTasks:
    @pytest.mark.asyncio
    async def test_list_tasks_requires_auth(self, client):
        resp = await client.get("/tasks/")
        assert resp.status_code == 403  # no bearer → 403

    @pytest.mark.asyncio
    async def test_create_and_list_task(self, client):
        with patch(
            "app.middleware.auth._decode_token",
            new=AsyncMock(return_value=_mock_token()),
        ):
            # Create
            resp = await client.post(
                "/tasks/",
                json={"title": "Buy groceries", "description": "Milk, eggs"},
                headers={"Authorization": "Bearer fake-token"},
            )
            assert resp.status_code == 201
            task_id = resp.json()["id"]

            # List
            resp = await client.get(
                "/tasks/", headers={"Authorization": "Bearer fake-token"}
            )
            assert resp.status_code == 200
            ids = [t["id"] for t in resp.json()]
            assert task_id in ids

    @pytest.mark.asyncio
    async def test_update_task_status(self, client):
        with patch(
            "app.middleware.auth._decode_token",
            new=AsyncMock(return_value=_mock_token()),
        ):
            resp = await client.post(
                "/tasks/",
                json={"title": "Test task"},
                headers={"Authorization": "Bearer fake-token"},
            )
            task_id = resp.json()["id"]

            resp = await client.patch(
                f"/tasks/{task_id}",
                json={"status": "in_progress"},
                headers={"Authorization": "Bearer fake-token"},
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_delete_task(self, client):
        with patch(
            "app.middleware.auth._decode_token",
            new=AsyncMock(return_value=_mock_token()),
        ):
            resp = await client.post(
                "/tasks/",
                json={"title": "To delete"},
                headers={"Authorization": "Bearer fake-token"},
            )
            task_id = resp.json()["id"]

            resp = await client.delete(
                f"/tasks/{task_id}",
                headers={"Authorization": "Bearer fake-token"},
            )
            assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_cannot_access_other_users_task(self, client):
        with patch(
            "app.middleware.auth._decode_token",
            new=AsyncMock(return_value=_mock_token(sub="user-A")),
        ):
            resp = await client.post(
                "/tasks/",
                json={"title": "User A task"},
                headers={"Authorization": "Bearer fake-token"},
            )
            task_id = resp.json()["id"]

        with patch(
            "app.middleware.auth._decode_token",
            new=AsyncMock(return_value=_mock_token(sub="user-B")),
        ):
            resp = await client.delete(
                f"/tasks/{task_id}",
                headers={"Authorization": "Bearer fake-token"},
            )
            assert resp.status_code == 404


class TestAdmin:
    @pytest.mark.asyncio
    async def test_admin_stats_requires_admin_role(self, client):
        with patch(
            "app.middleware.auth._decode_token",
            new=AsyncMock(return_value=_mock_token(groups=[])),  # no admin group
        ):
            resp = await client.get(
                "/admin/stats", headers={"Authorization": "Bearer fake-token"}
            )
            assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_stats_accessible_with_role(self, client):
        with patch(
            "app.middleware.auth._decode_token",
            new=AsyncMock(return_value=_mock_token(groups=["admin"])),
        ):
            resp = await client.get(
                "/admin/stats", headers={"Authorization": "Bearer fake-token"}
            )
            assert resp.status_code == 200
            assert "total_tasks" in resp.json()


class TestUsers:
    @pytest.mark.asyncio
    async def test_me_returns_user_info(self, client):
        with patch(
            "app.middleware.auth._decode_token",
            new=AsyncMock(return_value=_mock_token(sub="user-xyz")),
        ):
            resp = await client.get(
                "/users/me", headers={"Authorization": "Bearer fake-token"}
            )
            assert resp.status_code == 200
            assert resp.json()["sub"] == "user-xyz"

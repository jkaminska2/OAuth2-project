from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import health, tasks, users, admin

app = FastAPI(
    title="TaskManager API",
    description="REST API secured with OAuth 2.0 + PKCE via Authentik",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(admin.router)

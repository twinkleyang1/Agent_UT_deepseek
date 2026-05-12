"""UT Orchestrator Dashboard - FastAPI Backend"""
import os
import sys

# Ensure orchestrator src is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dashboard.backend.api.projects import router as projects_router
from dashboard.backend.api.state import router as state_router
from dashboard.backend.api.tasks import router as tasks_router
from dashboard.backend.api.ws import router as ws_router

app = FastAPI(title="UT Orchestrator Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(state_router)
app.include_router(tasks_router)
app.include_router(ws_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}

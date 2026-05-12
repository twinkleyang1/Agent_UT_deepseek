"""State query API routes."""
import os
from fastapi import APIRouter, HTTPException

from src.config import ProjectConfig
from src.state_manager import StateManager
from dashboard.backend.services.project_service import ProjectService

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REGISTRY_PATH = os.path.join(PROJECT_ROOT, "projects.json")

router = APIRouter(prefix="/api/projects/{project_id}", tags=["state"])


def _get_state(project_id: str) -> StateManager:
    svc = ProjectService(REGISTRY_PATH)
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    config_dict = {k: v for k, v in project.items() if k not in ("created_at", "status")}
    config = ProjectConfig(**config_dict)
    return StateManager(PROJECT_ROOT, config=config)


@router.get("/status")
async def get_status(project_id: str):
    sm = _get_state(project_id)
    return sm.get_summary()


@router.get("/classes")
async def get_classes(project_id: str):
    sm = _get_state(project_id)
    return sm.load_class_list()


@router.get("/coverage")
async def get_coverage(project_id: str):
    sm = _get_state(project_id)
    return sm.load_coverage_report()


@router.get("/coverage/history")
async def get_coverage_history(project_id: str):
    sm = _get_state(project_id)
    return sm.get_coverage_trend()

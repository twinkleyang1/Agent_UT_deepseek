"""Project CRUD API routes."""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional

from src.config import ProjectConfig
from src.state_manager import StateManager
from dashboard.backend.services.project_service import ProjectService

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REGISTRY_PATH = os.path.join(PROJECT_ROOT, "projects.json")

router = APIRouter(prefix="/api/projects", tags=["projects"])
svc = ProjectService(REGISTRY_PATH)


class ProjectCreate(BaseModel):
    id: str
    name: str = ""
    path: str
    maven_bin: str
    maven_settings: str = ""
    coverage_targets: Dict[str, float] = Field(default_factory=lambda: {"line": 0.70, "branch": 0.60})
    batch_size: int = 5


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    maven_bin: Optional[str] = None
    maven_settings: Optional[str] = None
    coverage_targets: Optional[Dict[str, float]] = None
    batch_size: Optional[int] = None


@router.get("")
async def list_projects():
    projects = svc.list_projects()
    result = []
    for p in projects:
        try:
            config_dict = {k: v for k, v in p.items() if k not in ("created_at", "status")}
            config = ProjectConfig(**config_dict)
            sm = StateManager(PROJECT_ROOT, config=config)
            p["summary"] = sm.get_summary()
        except Exception:
            p["summary"] = None
        result.append(p)
    return result


@router.post("")
async def create_project(body: ProjectCreate):
    existing = svc.get_project(body.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Project '{body.id}' already exists")
    return svc.add_project(
        id=body.id, name=body.name, path=body.path,
        maven_bin=body.maven_bin, maven_settings=body.maven_settings,
        coverage_targets=body.coverage_targets, batch_size=body.batch_size,
    )


@router.get("/{project_id}")
async def get_project(project_id: str):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        config_dict = {k: v for k, v in project.items() if k not in ("created_at", "status")}
        config = ProjectConfig(**config_dict)
        sm = StateManager(PROJECT_ROOT, config=config)
        project["summary"] = sm.get_summary()
    except Exception:
        project["summary"] = None
    return project


@router.post("/{project_id}")
async def update_project(project_id: str, body: ProjectUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = svc.update_project(project_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    if not svc.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}

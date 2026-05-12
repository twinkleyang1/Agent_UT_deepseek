"""API routes to trigger Celery tasks."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from dashboard.backend.tasks.orchestrator_tasks import scan_project, evaluate_coverage, run_loop
from dashboard.backend.services.project_service import ProjectService
from src.config import ProjectConfig
from src.orchestrator import Orchestrator
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REGISTRY_PATH = os.path.join(PROJECT_ROOT, "projects.json")

router = APIRouter(prefix="/api/projects/{project_id}", tags=["tasks"])


class LoopRequest(BaseModel):
    max_iterations: int = 200


def _get_config(project_id: str):
    svc = ProjectService(REGISTRY_PATH)
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    config_dict = {k: v for k, v in project.items() if k not in ("created_at", "status")}
    return ProjectConfig(**config_dict)


@router.post("/scan")
async def trigger_scan(project_id: str):
    task = scan_project.delay(project_id)
    return {"task_id": task.id, "status": "queued", "phase": "scan"}


@router.post("/dispatch")
async def trigger_dispatch(project_id: str):
    config = _get_config(project_id)
    orch = Orchestrator(project_root=PROJECT_ROOT, config=config)
    batch_info = orch.run_phase2()
    prompts = batch_info.get("prompts", [])
    return {
        "phase": "generate",
        "prompt_count": len(prompts),
        "prompts": [{"task": p["task"], "prompt": p["prompt"]} for p in prompts],
    }


@router.post("/evaluate")
async def trigger_evaluate(project_id: str):
    task = evaluate_coverage.delay(project_id)
    return {"task_id": task.id, "status": "queued", "phase": "evaluate"}


@router.post("/loop")
async def trigger_loop(project_id: str, body: LoopRequest = None):
    max_iter = body.max_iterations if body else 200
    task = run_loop.delay(project_id, max_iter)
    return {"task_id": task.id, "status": "queued", "phase": "loop"}

"""Celery tasks for orchestrator operations."""
import os
import json
import redis as sync_redis

from src.config import ProjectConfig
from src.orchestrator import Orchestrator
from dashboard.backend.services.project_service import ProjectService
from dashboard.backend.tasks.celery_app import celery_app

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REGISTRY_PATH = os.path.join(PROJECT_ROOT, "projects.json")

CHANNEL_PREFIX = "ut:project:"


def _get_orchestrator(project_id: str) -> Orchestrator:
    svc = ProjectService(REGISTRY_PATH)
    project = svc.get_project(project_id)
    if not project:
        raise ValueError(f"Project '{project_id}' not found")
    config_dict = {k: v for k, v in project.items() if k not in ("created_at", "status")}
    config = ProjectConfig(**config_dict)
    return Orchestrator(project_root=PROJECT_ROOT, config=config)


def _publish(project_id: str, message: dict):
    """Publish a message to the project's Redis channel."""
    try:
        r = sync_redis.Redis(host="localhost", port=6379, db=0)
        r.publish(f"{CHANNEL_PREFIX}{project_id}", json.dumps(message))
    except Exception:
        pass  # Redis might not be available


@celery_app.task(bind=True, name="scan_project")
def scan_project(self, project_id: str):
    _publish(project_id, {"type": "task_started", "task_id": self.request.id, "phase": "scan"})
    _publish(project_id, {"type": "log", "level": "info", "message": f"Scanning project {project_id}"})
    try:
        orch = _get_orchestrator(project_id)
        result = orch.run_phase1()
        class_count = len(result.get("classes", []))
        _publish(project_id, {"type": "log", "level": "info", "message": f"Scan complete: {class_count} classes"})
        _publish(project_id, {"type": "task_complete", "task_id": self.request.id, "result": result})
        return result
    except Exception as e:
        _publish(project_id, {"type": "log", "level": "error", "message": str(e)})
        raise


@celery_app.task(bind=True, name="evaluate_coverage")
def evaluate_coverage(self, project_id: str):
    _publish(project_id, {"type": "task_started", "task_id": self.request.id, "phase": "evaluate"})
    _publish(project_id, {"type": "log", "level": "info", "message": "Running tests and evaluating coverage..."})
    try:
        orch = _get_orchestrator(project_id)
        result = orch.run_phase3()
        cov = result.get("coverage", {})
        _publish(project_id, {"type": "coverage_update", "line": cov.get("line", 0), "branch": cov.get("branch", 0)})
        _publish(project_id, {"type": "log", "level": "info", "message": f"Coverage: line {cov.get('line', 0)*100:.1f}%, branch {cov.get('branch', 0)*100:.1f}%"})
        _publish(project_id, {"type": "task_complete", "task_id": self.request.id, "result": result})
        return result
    except Exception as e:
        _publish(project_id, {"type": "log", "level": "error", "message": str(e)})
        raise


@celery_app.task(bind=True, name="run_loop")
def run_loop(self, project_id: str, max_iterations: int = 200):
    _publish(project_id, {"type": "task_started", "task_id": self.request.id, "phase": "loop"})
    _publish(project_id, {"type": "log", "level": "info", "message": f"Starting full loop (max {max_iterations} iterations)"})
    try:
        orch = _get_orchestrator(project_id)
        result = orch.run(max_iterations=max_iterations)
        summary = result.get("summary", {})
        cov = summary.get("coverage", {})
        methods = summary.get("methods", {})
        _publish(project_id, {"type": "coverage_update", "line": cov.get("line", 0), "branch": cov.get("branch", 0)})
        _publish(project_id, {"type": "progress", "methods_pass": methods.get("pass", 0), "methods_total": methods.get("total", 0)})
        _publish(project_id, {"type": "task_complete", "task_id": self.request.id, "result": result})
        return result
    except Exception as e:
        _publish(project_id, {"type": "log", "level": "error", "message": str(e)})
        raise

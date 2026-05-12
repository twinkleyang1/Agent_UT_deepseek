"""Manages projects.json registry."""
import json
import os
from datetime import date
from typing import Any, Dict, List, Optional


class ProjectService:
    def __init__(self, registry_path: str):
        self.registry_path = registry_path

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.registry_path):
            return {"projects": []}
        with open(self.registry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_projects(self) -> List[Dict[str, Any]]:
        return self._load().get("projects", [])

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        for p in self.list_projects():
            if p["id"] == project_id:
                return p
        return None

    def add_project(self, id: str, path: str, maven_bin: str,
                    name: str = "", maven_settings: str = "",
                    coverage_targets: Dict[str, float] = None,
                    batch_size: int = 5) -> Dict[str, Any]:
        data = self._load()
        project = {
            "id": id,
            "name": name or id,
            "path": path,
            "maven_bin": maven_bin,
            "maven_settings": maven_settings,
            "coverage_targets": coverage_targets or {"line": 0.70, "branch": 0.60},
            "batch_size": batch_size,
            "created_at": date.today().isoformat(),
            "status": "active",
        }
        data["projects"].append(project)
        self._save(data)
        return project

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        data = self._load()
        for p in data["projects"]:
            if p["id"] == project_id:
                for k, v in updates.items():
                    if k in p and k != "id":
                        p[k] = v
                self._save(data)
                return p
        return None

    def delete_project(self, project_id: str) -> bool:
        data = self._load()
        before = len(data["projects"])
        data["projects"] = [p for p in data["projects"] if p["id"] != project_id]
        if len(data["projects"]) == before:
            return False
        self._save(data)
        return True

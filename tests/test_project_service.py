import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dashboard.backend.services.project_service import ProjectService


def test_list_projects_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = ProjectService(registry_path=os.path.join(tmpdir, "projects.json"))
        projects = svc.list_projects()
        assert projects == []


def test_add_and_get_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = ProjectService(registry_path=os.path.join(tmpdir, "projects.json"))
        project = svc.add_project(
            id="test-proj",
            name="Test Project",
            path="/data/projects/test",
            maven_bin="/usr/bin/mvn",
        )
        assert project["id"] == "test-proj"
        assert project["path"] == "/data/projects/test"
        assert project["status"] == "active"

        projects = svc.list_projects()
        assert len(projects) == 1

        p = svc.get_project("test-proj")
        assert p["name"] == "Test Project"


def test_delete_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = ProjectService(registry_path=os.path.join(tmpdir, "projects.json"))
        svc.add_project(id="tmp", name="Tmp", path="/tmp", maven_bin="/usr/bin/mvn")
        assert svc.delete_project("tmp") is True
        assert svc.get_project("tmp") is None
        assert svc.delete_project("nonexistent") is False


def test_update_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        svc = ProjectService(registry_path=os.path.join(tmpdir, "projects.json"))
        svc.add_project(id="upd", name="Old", path="/old", maven_bin="/usr/bin/mvn")
        updated = svc.update_project("upd", {"name": "New Name", "batch_size": 10})
        assert updated["name"] == "New Name"
        assert updated["batch_size"] == 10

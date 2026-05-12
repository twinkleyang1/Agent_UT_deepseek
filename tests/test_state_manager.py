# tests/test_state_manager.py
import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import ProjectConfig
from src.state_manager import StateManager


def test_state_manager_uses_project_shared_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ProjectConfig(
            id="test",
            path=tmpdir,
            maven_bin="/usr/bin/mvn",
        )
        sm = StateManager(project_root="/fake/orchestrator/root", config=config)
        assert sm.shared_dir == os.path.join(tmpdir, "shared")
        assert os.path.exists(sm.shared_dir)


def test_state_manager_save_and_load_class_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ProjectConfig(id="test", path=tmpdir, maven_bin="/usr/bin/mvn")
        sm = StateManager(project_root="/fake", config=config)

        data = {"project_path": tmpdir, "scan_date": "2026-05-12", "classes": []}
        sm.save_class_list(data)
        loaded = sm.load_class_list()
        assert loaded["project_path"] == tmpdir
        assert loaded["scan_date"] == "2026-05-12"

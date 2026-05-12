# tests/test_orchestrator.py
import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import ProjectConfig
from src.orchestrator import Orchestrator


def test_orchestrator_with_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ProjectConfig(
            id="test",
            path=tmpdir,
            maven_bin="/fake/mvn",
        )
        orch = Orchestrator(
            project_root="/fake/root",
            config=config,
        )
        assert orch.java_project_path == tmpdir
        assert orch.MAVEN_BIN == "/fake/mvn"


def test_orchestrator_shared_dir_uses_project_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ProjectConfig(
            id="test",
            path=tmpdir,
            maven_bin="/fake/mvn",
        )
        orch = Orchestrator(
            project_root="/fake/root",
            config=config,
        )
        assert orch.state.shared_dir == os.path.join(tmpdir, "shared")

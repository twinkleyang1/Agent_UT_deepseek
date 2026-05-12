# tests/test_config.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import ProjectConfig


def test_project_config_defaults():
    config = ProjectConfig(
        id="test-proj",
        path="/tmp/test-java-project",
        maven_bin="/usr/bin/mvn",
    )
    assert config.id == "test-proj"
    assert config.path == "/tmp/test-java-project"
    assert config.maven_bin == "/usr/bin/mvn"
    assert config.maven_settings == ""
    assert config.coverage_targets == {"line": 0.70, "branch": 0.60}
    assert config.name == "test-proj"
    assert config.batch_size == 5


def test_project_config_full():
    config = ProjectConfig(
        id="full-proj",
        name="Full Project",
        path="/data/projects/full",
        maven_bin="/opt/maven/bin/mvn",
        maven_settings="/opt/maven/conf/settings.xml",
        coverage_targets={"line": 0.80, "branch": 0.65},
        batch_size=8,
    )
    assert config.name == "Full Project"
    assert config.maven_settings == "/opt/maven/conf/settings.xml"
    assert config.coverage_targets["line"] == 0.80
    assert config.batch_size == 8


def test_project_config_paths():
    config = ProjectConfig(
        id="test",
        path="/data/projects/test",
        maven_bin="/usr/bin/mvn",
    )
    assert config.shared_dir == "/data/projects/test/shared"
    assert config.src_main_java == "/data/projects/test/src/main/java"
    assert config.src_test_java == "/data/projects/test/src/test/java"

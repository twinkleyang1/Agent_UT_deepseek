# tests/test_subagent_dispatch.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import ProjectConfig
from src.subagent_dispatch import SubagentDispatch


def test_subagent_dispatch_with_config():
    config = ProjectConfig(
        id="test",
        path="/data/projects/test",
        maven_bin="/custom/mvn",
        coverage_targets={"line": 0.80, "branch": 0.65},
    )
    disp = SubagentDispatch("/fake/root", config=config)
    assert disp.MAVEN_BIN == "/custom/mvn"
    assert disp.java_project_path == "/data/projects/test"
    assert disp.COVERAGE_TARGET_LINE == 0.80
    assert disp.COVERAGE_TARGET_BRANCH == 0.65


def test_subagent_dispatch_without_config_backward_compat():
    disp = SubagentDispatch("/fake/root", java_project="dianping")
    assert disp.java_project == "dianping"
    assert disp.MAVEN_BIN == "/home/twinkle/app/maven/bin/mvn"

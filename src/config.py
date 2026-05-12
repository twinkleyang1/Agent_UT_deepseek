# src/config.py
from dataclasses import dataclass, field
from typing import Dict
import os


@dataclass
class ProjectConfig:
    """Configuration for a single Java project under test.

    When `name` is empty, it falls back to `id`.
    """
    id: str
    path: str
    maven_bin: str
    name: str = ""
    maven_settings: str = ""
    coverage_targets: Dict[str, float] = field(default_factory=lambda: {"line": 0.70, "branch": 0.60})
    batch_size: int = 5

    def __post_init__(self):
        if not self.name:
            self.name = self.id

    @property
    def shared_dir(self) -> str:
        return os.path.join(self.path, "shared")

    @property
    def src_main_java(self) -> str:
        return os.path.join(self.path, "src", "main", "java")

    @property
    def src_test_java(self) -> str:
        return os.path.join(self.path, "src", "test", "java")

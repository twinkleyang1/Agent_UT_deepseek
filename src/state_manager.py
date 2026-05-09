"""
State Manager - manages state files in shared/ directory.

State files:
  - class_list.json: Full class and method inventory with test status
  - test_plan.json: Test generation plan and iteration tracking
  - progress.txt: Human-readable progress log
  - coverage_report.json: Coverage metrics and quality scores
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class StateManager:
    """Manages state files for the UT generation orchestrator."""

    SHARED_DIR = "shared"
    CLASS_LIST = "class_list.json"
    TEST_PLAN = "test_plan.json"
    PROGRESS = "progress.txt"
    COVERAGE_REPORT = "coverage_report.json"

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.shared_dir = os.path.join(project_root, self.SHARED_DIR)
        os.makedirs(self.shared_dir, exist_ok=True)

    def _path(self, filename: str) -> str:
        return os.path.join(self.shared_dir, filename)

    # ==================== Existence Checks ====================

    def is_initialized(self) -> bool:
        return os.path.exists(self._path(self.CLASS_LIST)) and \
               os.path.exists(self._path(self.TEST_PLAN))

    # ==================== Class List ====================

    def load_class_list(self) -> Dict[str, Any]:
        path = self._path(self.CLASS_LIST)
        if not os.path.exists(path):
            return {"project_path": "", "scan_date": "", "classes": []}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_class_list(self, data: Dict[str, Any]) -> None:
        with open(self._path(self.CLASS_LIST), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_pending_methods(self) -> List[Dict[str, Any]]:
        """Get all methods with test_status='pending', grouped by priority."""
        data = self.load_class_list()
        pending = []
        for cls in data.get("classes", []):
            for method in cls.get("methods", []):
                if method.get("test_status") == "pending":
                    pending.append({
                        "class_name": cls["name"],
                        "package": cls["package"],
                        "class_path": cls["path"],
                        "test_file": cls.get("test_file", ""),
                        "type": cls.get("type", "other"),
                        "priority": cls.get("priority", 5),
                        "method_name": method["name"],
                        "signature": method["signature"],
                        "test_method": method.get("test_method", ""),
                        "complexity": method.get("complexity", "medium"),
                    })
        return sorted(pending, key=lambda m: m["priority"])

    def get_methods_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all methods with a given test_status."""
        data = self.load_class_list()
        results = []
        for cls in data.get("classes", []):
            for method in cls.get("methods", []):
                if method.get("test_status") == status:
                    results.append({
                        "class_name": cls["name"],
                        "method_name": method["name"],
                        "test_method": method.get("test_method", ""),
                    })
        return results

    def update_method_status(self, class_name: str, method_name: str,
                             test_status: str, **kwargs) -> None:
        """Update the test_status of a specific method."""
        data = self.load_class_list()
        for cls in data.get("classes", []):
            if cls["name"] == class_name:
                for method in cls.get("methods", []):
                    if method["name"] == method_name:
                        method["test_status"] = test_status
                        for k, v in kwargs.items():
                            method[k] = v
                        break
                break
        self.save_class_list(data)

    def mark_method_in_progress(self, class_name: str, method_name: str) -> None:
        self.update_method_status(class_name, method_name, "in_progress")

    def mark_method_pass(self, class_name: str, method_name: str) -> None:
        self.update_method_status(class_name, method_name, "pass")

    def mark_method_fail(self, class_name: str, method_name: str, error: str = "") -> None:
        self.update_method_status(class_name, method_name, "fail", error=error)

    def count_by_status(self) -> Dict[str, int]:
        data = self.load_class_list()
        counts = {"pending": 0, "in_progress": 0, "pass": 0, "fail": 0}
        for cls in data.get("classes", []):
            for method in cls.get("methods", []):
                s = method.get("test_status", "pending")
                counts[s] = counts.get(s, 0) + 1
        return counts

    def total_methods(self) -> int:
        data = self.load_class_list()
        return sum(len(cls.get("methods", [])) for cls in data.get("classes", []))

    # ==================== Test Plan ====================

    def load_test_plan(self) -> Dict[str, Any]:
        path = self._path(self.TEST_PLAN)
        if not os.path.exists(path):
            return {
                "plan_version": "1.0",
                "iteration": 0,
                "coverage_target": {"line": 0.70, "branch": 0.60},
                "batch_size": 5,
                "current_batch": [],
                "completed_methods": 0,
                "total_methods": 0,
                "failed_methods": [],
            }
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_test_plan(self, data: Dict[str, Any]) -> None:
        with open(self._path(self.TEST_PLAN), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def increment_iteration(self) -> int:
        plan = self.load_test_plan()
        plan["iteration"] = plan.get("iteration", 0) + 1
        plan["completed_methods"] = self.count_by_status().get("pass", 0)
        plan["total_methods"] = self.total_methods()
        self.save_test_plan(plan)
        return plan["iteration"]

    def set_current_batch(self, class_names: List[str]) -> None:
        plan = self.load_test_plan()
        plan["current_batch"] = class_names
        self.save_test_plan(plan)

    def record_failed_method(self, class_name: str, method_name: str, reason: str) -> None:
        plan = self.load_test_plan()
        plan.setdefault("failed_methods", []).append({
            "class": class_name,
            "method": method_name,
            "reason": reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        self.save_test_plan(plan)

    # ==================== Progress ====================

    def load_progress(self) -> str:
        path = self._path(self.PROGRESS)
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def save_progress(self, content: str) -> None:
        with open(self._path(self.PROGRESS), "w", encoding="utf-8") as f:
            f.write(content)

    def write_progress_summary(self, iteration: int, batch_results: List[Dict],
                                coverage: Dict[str, float]) -> None:
        """Write a structured progress summary."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        counts = self.count_by_status()
        total = sum(counts.values())

        lines = [
            "# UT Generation Progress",
            f"Last Updated: {now}",
            f"Iteration: {iteration}",
            "",
            "## Stats",
            f"- Methods tested: {counts.get('pass', 0)}/{total} "
            f"({counts.get('pass', 0)/max(total,1)*100:.1f}%)",
            f"- Coverage: Line {coverage.get('line', 0)*100:.0f}%, "
            f"Branch {coverage.get('branch', 0)*100:.0f}%",
            "",
        ]

        if batch_results:
            lines.append(f"## Last Batch (Iteration {iteration})")
            for r in batch_results:
                status = "✓" if r.get("status") == "pass" else "✗"
                lines.append(
                    f"- {status} {r.get('class_name')}.{r.get('method_name')}"
                    f" ({r.get('status')}, {r.get('duration_ms', 0)}ms)"
                )
            lines.append("")

        pending = self.get_pending_methods()[:10]
        if pending:
            lines.append("## Pending Priority (Next Batch)")
            for p in pending:
                lines.append(f"- {p['class_name']}.{p['method_name']}")
            lines.append("")

        self.save_progress("\n".join(lines))

    # ==================== Coverage Report ====================

    def load_coverage_report(self) -> Dict[str, Any]:
        path = self._path(self.COVERAGE_REPORT)
        if not os.path.exists(path):
            return {
                "report_date": "",
                "overall_coverage": {"line": 0.0, "branch": 0.0, "method": 0.0},
                "class_results": [],
                "sprint_status": "pending",
            }
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_coverage_report(self, data: Dict[str, Any]) -> None:
        data["report_date"] = datetime.now().strftime("%Y-%m-%d")
        with open(self._path(self.COVERAGE_REPORT), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def coverage_targets_met(self) -> bool:
        report = self.load_coverage_report()
        cov = report.get("overall_coverage", {})
        return cov.get("line", 0) >= 0.70 and cov.get("branch", 0) >= 0.60

    # ==================== Phase Detection ====================

    def detect_phase(self) -> str:
        """
        Determine the current orchestration phase.

        Returns:
            'init': First run, need to scan project
            'generate': Have pending methods to test
            'evaluate': All methods tested, need coverage check
            'complete': Coverage targets met
        """
        if not self.is_initialized():
            return "init"

        counts = self.count_by_status()
        if counts.get("pending", 0) > 0:
            return "generate"

        if self.coverage_targets_met():
            return "complete"

        # All methods tested but coverage not met -> evaluate
        if counts.get("pending", 0) == 0 and counts.get("in_progress", 0) == 0:
            return "evaluate"

        return "generate"

    def get_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of current state."""
        counts = self.count_by_status()
        coverage = self.load_coverage_report().get("overall_coverage", {})
        total = sum(counts.values())
        return {
            "phase": self.detect_phase(),
            "initialized": self.is_initialized(),
            "methods": {
                "total": total,
                "pass": counts.get("pass", 0),
                "fail": counts.get("fail", 0),
                "pending": counts.get("pending", 0),
                "in_progress": counts.get("in_progress", 0),
            },
            "coverage": {
                "line": coverage.get("line", 0.0),
                "branch": coverage.get("branch", 0.0),
                "method": coverage.get("method", 0.0),
            },
            "targets_met": self.coverage_targets_met(),
        }

    # ==================== Reset ====================

    def reset(self) -> None:
        for fname in [self.CLASS_LIST, self.TEST_PLAN, self.PROGRESS, self.COVERAGE_REPORT]:
            path = self._path(fname)
            if os.path.exists(path):
                os.remove(path)

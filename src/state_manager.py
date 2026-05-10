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
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class StateManager:
    """Manages state files for the UT generation orchestrator."""

    SHARED_DIR = "shared"
    CLASS_LIST = "class_list.json"
    TEST_PLAN = "test_plan.json"
    PROGRESS = "progress.txt"
    COVERAGE_REPORT = "coverage_report.json"
    COVERAGE_HISTORY = "coverage_history.json"

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

    def get_pending_methods_by_class(self) -> List[Dict[str, Any]]:
        """Get classes with pending methods, each containing all methods.

        Returns per-class dicts for dispatching one subagent per class.
        """
        data = self.load_class_list()
        result = []
        for cls in data.get("classes", []):
            methods = cls.get("methods", [])
            all_methods = [{
                "name": m["name"],
                "signature": m.get("signature", ""),
                "test_method": m.get("test_method", ""),
                "complexity": m.get("complexity", "medium"),
                "test_status": m.get("test_status", "pending"),
            } for m in methods]

            pending_methods = [m for m in all_methods
                              if m["test_status"] == "pending"]
            if not pending_methods:
                continue

            complexity_order = {"complex": 3, "medium": 2, "simple": 1}
            overall_complexity = max(
                all_methods,
                key=lambda m: complexity_order.get(
                    m.get("complexity", "medium"), 2)
            ).get("complexity", "medium")

            result.append({
                "class_name": cls["name"],
                "package": cls["package"],
                "class_path": cls["path"],
                "test_file": cls.get("test_file", ""),
                "type": cls.get("type", "other"),
                "priority": cls.get("priority", 5),
                "class_coverage_status": cls.get("class_coverage_status",
                                                  "pending"),
                "class_line_coverage": cls.get("class_line_coverage", 0.0),
                "class_branch_coverage": cls.get("class_branch_coverage", 0.0),
                "class_methods": all_methods,
                "complexity": overall_complexity,
            })
        return sorted(result,
                      key=lambda c: (c["priority"],
                                     -len(c["class_methods"])))

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

    def set_class_coverage_status(self, class_name: str, status: str,
                                   line_coverage: float = 0.0,
                                   branch_coverage: float = 0.0) -> None:
        """Set class-level coverage tracking fields."""
        data = self.load_class_list()
        for cls in data.get("classes", []):
            if cls["name"] == class_name:
                cls["class_coverage_status"] = status
                cls["class_line_coverage"] = round(line_coverage, 4)
                cls["class_branch_coverage"] = round(branch_coverage, 4)
                cls["class_coverage_timestamp"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S")
                break
        self.save_class_list(data)

    def mark_class_in_progress(self, class_name: str) -> None:
        self.set_class_coverage_status(class_name, "in_progress")

    def mark_class_met_targets(self, class_name: str,
                                line_coverage: float,
                                branch_coverage: float) -> None:
        self.set_class_coverage_status(class_name, "met_targets",
                                        line_coverage, branch_coverage)

    def mark_class_exhausted(self, class_name: str,
                              line_coverage: float,
                              branch_coverage: float) -> None:
        self.set_class_coverage_status(class_name, "exhausted",
                                        line_coverage, branch_coverage)

    def mark_class_failed(self, class_name: str, error: str = "") -> None:
        self.set_class_coverage_status(class_name, "failed")
        data = self.load_class_list()
        for cls in data.get("classes", []):
            if cls["name"] == class_name:
                cls["class_error"] = error
                break
        self.save_class_list(data)

    def reset_class_in_progress(self, class_name: str) -> None:
        """Revert in_progress methods back to pending (on subagent failure)."""
        data = self.load_class_list()
        for cls in data.get("classes", []):
            if cls["name"] == class_name:
                for m in cls.get("methods", []):
                    if m.get("test_status") == "in_progress":
                        m["test_status"] = "pending"
                break
        self.save_class_list(data)

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
                rstatus = r.get("status", "fail")
                if rstatus in ("class_complete", "pass"):
                    icon = "✓"
                elif rstatus == "class_partial":
                    icon = "~"
                else:
                    icon = "✗"
                class_cov = r.get("class_coverage", {})
                cov_str = ""
                if class_cov:
                    cov_str = (f" L:{class_cov.get('line_coverage', 0)*100:.0f}%"
                               f" B:{class_cov.get('branch_coverage', 0)*100:.0f}%")
                test_count = len(r.get("test_results", []))
                lines.append(
                    f"- {icon} {r.get('class_name', '?')}"
                    f" ({rstatus}{cov_str} tests={test_count})"
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

    # ==================== Per-Method Coverage Tracking ====================

    def record_method_coverage(self, class_name: str, method_name: str,
                                line_coverage: float, branch_coverage: float) -> None:
        """
        Record per-class coverage snapshot after a subagent writes a test.
        The coverage is class-level (jacoco.csv granularity), stored per-method
        for historical tracking.

        Updates both class_list.json (method-level) and coverage_history.json.
        """
        # Update method entry in class_list
        data = self.load_class_list()
        for cls in data.get("classes", []):
            if cls["name"] == class_name:
                for method in cls.get("methods", []):
                    if method["name"] == method_name:
                        method["last_line_coverage"] = round(line_coverage, 4)
                        method["last_branch_coverage"] = round(branch_coverage, 4)
                        method["coverage_timestamp"] = datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S")
                        break
                break
        self.save_class_list(data)

        # Append to coverage history for trend analysis
        history = self._load_coverage_history()
        history.append({
            "class_name": class_name,
            "method_name": method_name,
            "line_coverage": round(line_coverage, 4),
            "branch_coverage": round(branch_coverage, 4),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        self._save_coverage_history(history)

    def get_class_coverage_snapshot(self, class_name: str) -> Dict[str, Any]:
        """Get the latest coverage snapshot for a class from its methods."""
        data = self.load_class_list()
        for cls in data.get("classes", []):
            if cls["name"] == class_name:
                coverages = []
                for m in cls.get("methods", []):
                    if "last_line_coverage" in m:
                        coverages.append({
                            "method": m["name"],
                            "line": m.get("last_line_coverage", 0),
                            "branch": m.get("last_branch_coverage", 0),
                            "timestamp": m.get("coverage_timestamp", ""),
                        })
                return {
                    "class_name": class_name,
                    "method_snapshots": coverages,
                }
        return {"class_name": class_name, "method_snapshots": []}

    def get_coverage_trend(self, class_name: str = None) -> List[Dict[str, Any]]:
        """Get coverage trend over time, optionally filtered by class."""
        history = self._load_coverage_history()
        if class_name:
            history = [h for h in history if h["class_name"] == class_name]
        return history

    def get_low_coverage_methods(self, line_threshold: float = 0.3,
                                  branch_threshold: float = 0.2) -> List[Dict[str, Any]]:
        """
        Get methods whose classes have low coverage, for re-prioritization.
        Returns methods sorted by coverage (lowest first).
        """
        data = self.load_class_list()
        low_cov = []
        for cls in data.get("classes", []):
            # Get latest coverage from methods
            latest_line = 0.0
            latest_branch = 0.0
            for m in cls.get("methods", []):
                if "last_line_coverage" in m:
                    latest_line = max(latest_line, m.get("last_line_coverage", 0))
                    latest_branch = max(latest_branch, m.get("last_branch_coverage", 0))

            if latest_line < line_threshold or latest_branch < branch_threshold:
                for m in cls.get("methods", []):
                    if m.get("test_status") == "pending":
                        low_cov.append({
                            "class_name": cls["name"],
                            "package": cls["package"],
                            "class_path": cls["path"],
                            "test_file": cls.get("test_file", ""),
                            "type": cls.get("type", "other"),
                            "priority": cls.get("priority", 5),
                            "method_name": m["name"],
                            "signature": m["signature"],
                            "test_method": m.get("test_method", ""),
                            "complexity": m.get("complexity", "medium"),
                            "current_line_coverage": latest_line,
                            "current_branch_coverage": latest_branch,
                        })

        # Sort by coverage (lowest first), then by complexity
        complexity_order = {"complex": 0, "medium": 1, "simple": 2}
        low_cov.sort(key=lambda m: (
            m["current_line_coverage"],
            m["current_branch_coverage"],
            complexity_order.get(m.get("complexity", "medium"), 3),
        ))
        return low_cov

    # ==================== Coverage History Persistence ====================

    def _load_coverage_history(self) -> List[Dict[str, Any]]:
        path = self._path(self.COVERAGE_HISTORY)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_coverage_history(self, data: List[Dict[str, Any]]) -> None:
        with open(self._path(self.COVERAGE_HISTORY), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ==================== Phase Detection ====================

    def detect_phase(self, partial_eval_interval: int = 20) -> str:
        """
        Determine the current orchestration phase.

        Supports partial evaluation: if enough methods have been
        tested since the last evaluation, trigger evaluate early
        rather than waiting for ALL methods.

        Args:
            partial_eval_interval: Trigger evaluation after this many
                                   new pass/fail methods since last eval.

        Returns:
            'init': First run, need to scan project
            'generate': Have pending methods to test
            'evaluate': All methods tested (or partial eval triggered),
                        need coverage check
            'complete': Coverage targets met
        """
        if not self.is_initialized():
            return "init"

        counts = self.count_by_status()

        if self.coverage_targets_met():
            return "complete"

        # All methods tested but coverage not met -> evaluate
        if counts.get("pending", 0) == 0 and counts.get("in_progress", 0) == 0:
            return "evaluate"

        # Partial evaluation: trigger evaluate every N new methods
        if counts.get("pending", 0) > 0:
            tested_since_eval = counts.get("pass", 0) + counts.get("fail", 0)
            plan = self.load_test_plan()
            last_eval_count = plan.get("last_eval_completed", 0)
            if tested_since_eval - last_eval_count >= partial_eval_interval:
                return "evaluate"

        if counts.get("pending", 0) > 0:
            return "generate"

        return "generate"

    def mark_evaluation_complete(self) -> None:
        """Record the current pass+fail count after an evaluation."""
        plan = self.load_test_plan()
        counts = self.count_by_status()
        plan["last_eval_completed"] = counts.get("pass", 0) + counts.get("fail", 0)
        self.save_test_plan(plan)

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

    def get_per_class_coverage(self) -> List[Dict[str, Any]]:
        """Get per-class coverage data from coverage report."""
        report = self.load_coverage_report()
        return report.get("overall_coverage", {}).get("per_class", [])

    def get_classes_by_coverage(self, ascending: bool = True) -> List[Dict[str, Any]]:
        """
        Get classes sorted by coverage for prioritization.
        ascending=True: lowest coverage first (prioritize these).
        """
        per_class = self.get_per_class_coverage()
        per_class.sort(key=lambda c: c.get("line_coverage", 0),
                       reverse=not ascending)
        return per_class

    # ==================== Sync Existing Tests ====================

    def sync_existing_tests(self, test_src_dir: str) -> Dict[str, int]:
        """
        Scan existing test files and mark corresponding methods as tested.

        Two matching strategies:
        1. Exact name match: generated test_method name exists as @Test method
        2. Fuzzy match: test class exists with @Test methods → likely covers the class

        This is useful when:
        - Tests were written outside the orchestrator
        - Resuming after manual test additions
        - Initial scan of an already-partially-tested project
        """
        synced = 0
        skipped = 0
        classes_with_tests = 0
        data = self.load_class_list()

        # Build a map of test class names to their test files
        existing_tests = {}
        if os.path.exists(test_src_dir):
            for root, dirs, files in os.walk(test_src_dir):
                for f in files:
                    if f.endswith("Test.java") or f.endswith("Tests.java"):
                        class_name = f.replace(".java", "")
                        existing_tests[class_name] = os.path.join(root, f)

        for cls in data.get("classes", []):
            test_class_name = cls["name"] + "Test"
            if test_class_name not in existing_tests:
                # Also check if test exists under a slightly different name
                alt_names = [n for n in existing_tests if n.startswith(cls["name"])]
                if not alt_names:
                    skipped += len(cls.get("methods", []))
                    continue
                test_file_path = existing_tests[alt_names[0]]
            else:
                test_file_path = existing_tests[test_class_name]

            try:
                with open(test_file_path, "r", encoding="utf-8") as tf:
                    test_content = tf.read()
            except (IOError, UnicodeDecodeError):
                skipped += len(cls.get("methods", []))
                continue

            # Find @Test methods in the test file
            test_methods = set()
            for m in re.finditer(r'@Test.*?\n.*?void\s+(\w+)\s*\(', test_content):
                test_methods.add(m.group(1))

            if not test_methods:
                skipped += len(cls.get("methods", []))
                continue

            classes_with_tests += 1

            # Track method name variants in test methods for fuzzy matching
            test_methods_lower = {t.lower() for t in test_methods}

            for method in cls.get("methods", []):
                if method.get("test_status") in ("pass", "fail", "in_progress"):
                    continue

                method_name = method["name"].lower()
                expected = method.get("test_method", "").lower()

                # Strategy 1: Exact match with generated test_method name
                if expected and any(expected == t.lower() for t in test_methods):
                    method["test_status"] = "pass"
                    method["synced"] = True
                    synced += 1
                    continue

                # Strategy 2: Look for any test method containing the source method name
                found_fuzzy = any(
                    method_name in t.lower() or t.lower().startswith("should")
                    for t in test_methods
                )
                if found_fuzzy and len(test_methods) >= len(cls.get("methods", [])) * 0.5:
                    # If test class has decent coverage, trust it
                    method["test_status"] = "pass"
                    method["synced"] = True
                    synced += 1
                else:
                    skipped += 1

        if synced > 0:
            self.save_class_list(data)

        return {
            "synced": synced,
            "skipped": skipped,
            "classes_with_tests": classes_with_tests,
        }

    # ==================== Reset ====================

    def reset(self) -> None:
        for fname in [self.CLASS_LIST, self.TEST_PLAN, self.PROGRESS,
                      self.COVERAGE_REPORT, self.COVERAGE_HISTORY]:
            path = self._path(fname)
            if os.path.exists(path):
                os.remove(path)

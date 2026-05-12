"""
Orchestrator - core orchestration logic for UT generation.

Coordinates the three-phase lifecycle:
  Phase 1 - Scan & Plan: Scan Java project, create class_list + test_plan
  Phase 2 - Dispatch: Parallel dispatch of subagents to write tests
  Phase 3 - Evaluate & Loop: Run full test suite, check coverage, loop
"""

import json
import os
import re
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import ProjectConfig

from .state_manager import StateManager
from .subagent_dispatch import SubagentDispatch


class Orchestrator:
    """Core orchestrator for the UT generation system."""

    MAVEN_BIN = "/home/twinkle/app/maven/bin/mvn"

    # Priority by class type (lower = higher priority)
    TYPE_PRIORITY = {
        "entity": 1,
        "config": 2,
        "utils": 2,
        "controller": 3,
        "service": 4,
        "interceptor": 5,
        "mapper": 6,
        "other": 7,
    }

    # Classes to skip — only skip app entry points and pure exception classes
    SKIP_PATTERNS = [
        r".*Application$",
        r".*Exception$",
    ]

    def __init__(self, project_root: str, java_project: str = "dianping",
                 config: Optional["ProjectConfig"] = None):
        self.project_root = project_root
        if config:
            self.java_project_path = config.path
            self.MAVEN_BIN = config.maven_bin
            self.state = StateManager(project_root, config=config)
            self.dispatcher = SubagentDispatch(project_root, java_project)
        else:
            self.java_project = java_project
            self.java_project_path = os.path.join(project_root, java_project)
            self.state = StateManager(project_root)
            self.dispatcher = SubagentDispatch(project_root, java_project)

    # ==================== Phase 1: Scan & Plan ====================

    def should_skip_class(self, class_name: str) -> bool:
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, class_name):
                return True
        return False

    def classify_type(self, class_name: str, package: str) -> str:
        """Classify a Java class by its name and package."""
        name_lower = class_name.lower()
        pkg_lower = package.lower() if package else ""

        if "controller" in pkg_lower or "controller" in name_lower:
            return "controller"
        if "service" in pkg_lower and "impl" in pkg_lower:
            return "service"
        if "service" in pkg_lower:
            return "service"
        if "interceptor" in pkg_lower or "interceptor" in name_lower or "filter" in pkg_lower:
            return "interceptor"
        if "config" in pkg_lower or "configuration" in pkg_lower:
            return "config"
        if "mapper" in pkg_lower or "dao" in pkg_lower or "repository" in pkg_lower:
            return "mapper"
        if "entity" in pkg_lower or "model" in pkg_lower or "domain" in pkg_lower or "dto" in pkg_lower:
            return "entity"
        if "utils" in pkg_lower or "util" in pkg_lower or "helper" in pkg_lower:
            return "utils"
        return "other"

    def extract_methods(self, filepath: str) -> List[Dict[str, str]]:
        """Extract public method signatures from a Java source file."""
        methods = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return methods

        class_name = os.path.splitext(os.path.basename(filepath))[0]

        # Remove single-line comments and strings to avoid false matches
        cleaned = re.sub(r'//[^\n]*', '', content)
        cleaned = re.sub(r'"[^"]*"', '""', cleaned)

        # Match public methods including preceding annotations on separate lines
        pattern = re.compile(
            r'(?:@\w+(?:\([^)]*\))?\s*\n\s*)*'  # annotations (multi-line)
            r'public\s+(?:static\s+)?(?:final\s+)?'
            r'(?:abstract\s+)?(?:synchronized\s+)?'
            r'(?:<[^>]*>\s+)?'  # generic type param
            r'([\w.<>\[\],\s]+?)\s+'  # return type
            r'(\w+)\s*'  # method name
            r'\((.*?)\)',  # parameters (non-greedy)
            re.MULTILINE | re.DOTALL
        )

        # Backward pass to fix: DOTALL makes . match newlines in params too broadly,
        # so we use a two-pass approach: find method signatures line-oriented first
        line_pattern = re.compile(
            r'^\s*public\s+(?:static\s+)?(?:final\s+)?'
            r'(?:abstract\s+)?(?:synchronized\s+)?'
            r'([\w\s.<>\[\],]+?)\s+'  # return type
            r'(\w+)\s*'  # method name
            r'\(',  # opening paren
            re.MULTILINE
        )

        for match in line_pattern.finditer(cleaned):
            return_type = match.group(1).strip()
            method_name = match.group(2)

            # Skip constructors
            if method_name == class_name:
                continue

            # Skip getters/setters for entities (optional: reduce noise)
            if self._is_trivial_getter_setter(method_name, cleaned, match.end()):
                continue

            # Extract parameters by finding closing paren
            paren_start = match.end() - 1  # the '('
            paren_depth = 0
            params_end = paren_start
            for i in range(paren_start, min(paren_start + 2000, len(cleaned))):
                if cleaned[i] == '(':
                    paren_depth += 1
                elif cleaned[i] == ')':
                    paren_depth -= 1
                    if paren_depth == 0:
                        params_end = i
                        break

            params = cleaned[paren_start + 1:params_end].strip()
            # Collapse multi-line params to single line for signature
            params_compact = re.sub(r'\s+', ' ', params)

            # Determine complexity
            method_body_start = params_end + 1
            complexity = self._estimate_complexity(cleaned, method_body_start, method_name)

            test_method_name = self._generate_test_method_name(method_name, return_type)

            methods.append({
                "name": method_name,
                "signature": f"public {return_type} {method_name}({params_compact})",
                "test_status": "pending",
                "test_method": test_method_name,
                "complexity": complexity,
            })

        return methods

    def _is_trivial_getter_setter(self, method_name: str, content: str, pos: int) -> bool:
        """Detect if a method is a trivial getter/setter to optionally skip."""
        if not (method_name.startswith("get") or method_name.startswith("set")
                or method_name.startswith("is")):
            return False
        # Look ahead for simple one-liner body
        body_start = content.find("{", pos)
        body_end = content.find("}", body_start) if body_start != -1 else -1
        if body_start != -1 and body_end != -1:
            body = content[body_start:body_end]
            # Simple getter: return this.field;
            # Simple setter: this.field = field;
            if len(body.split("\n")) <= 2 and ("return this." in body or "this." in body):
                return True
        return False

    def _estimate_complexity(self, content: str, start: int, method_name: str) -> str:
        """Estimate method complexity from body size and branching."""
        # Find matching closing brace
        depth = 0
        body_start = content.find("{", start)
        if body_start == -1:
            return "simple"
        i = body_start
        while i < len(content):
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = content[body_start:i]

        lines = body.count("\n")
        branches = len(re.findall(r'\b(if|for|while|switch|catch)\b', body))

        if lines < 10 and branches <= 1:
            return "simple"
        elif lines < 30 and branches <= 5:
            return "medium"
        else:
            return "complex"

    def _generate_test_method_name(self, method_name: str, return_type: str) -> str:
        """Generate a standard test method name."""
        # Convert camelCase to readable
        readable = re.sub(r'([A-Z])', r' \1', method_name).strip()
        parts = readable.lower().split()

        if return_type.lower() in ("void", "boolean"):
            return f"should{method_name[0].upper() + method_name[1:]}Successfully"
        else:
            return f"shouldReturn{return_type.capitalize()}When{method_name[0].upper() + method_name[1:]}"

    def scan_project(self) -> Dict[str, Any]:
        """Phase 1: Scan the Java project and build class_list.json."""
        src_dir = os.path.join(self.java_project_path, "src", "main", "java")
        classes = []

        for root, dirs, files in os.walk(src_dir):
            java_files = [f for f in files if f.endswith(".java")]
            for jf in java_files:
                class_name = jf.replace(".java", "")
                if self.should_skip_class(class_name):
                    continue

                filepath = os.path.join(root, jf)
                rel_path = os.path.relpath(filepath, self.java_project_path)

                # Derive package from directory structure
                rel_dir = os.path.relpath(root, src_dir)
                package = rel_dir.replace(os.sep, ".")

                class_type = self.classify_type(class_name, package)
                priority = self.TYPE_PRIORITY.get(class_type, 6)

                # Build test file path
                test_rel = rel_path.replace("src/main/java", "src/test/java")
                test_rel = test_rel.replace(".java", "Test.java")

                methods = self.extract_methods(filepath)

                classes.append({
                    "name": class_name,
                    "package": package,
                    "path": rel_path,
                    "type": class_type,
                    "priority": priority,
                    "test_file": test_rel,
                    "methods": methods,
                })

        # Sort by priority
        classes.sort(key=lambda c: (c["priority"], c["name"]))

        return {
            "project_path": self.java_project_path,
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "classes": classes,
        }

    def build_test_plan(self, class_list: Dict[str, Any]) -> Dict[str, Any]:
        """Build initial test_plan.json from class list."""
        total_methods = sum(
            len(cls.get("methods", [])) for cls in class_list.get("classes", [])
        )

        return {
            "plan_version": "1.0",
            "iteration": 0,
            "coverage_target": {"line": 0.70, "branch": 0.60},
            "batch_size": 5,
            "current_batch": [],
            "completed_methods": 0,
            "total_methods": total_methods,
            "failed_methods": [],
        }

    def run_phase1(self) -> Dict[str, Any]:
        """Execute Phase 1: Scan & Plan. Returns summary."""
        print("=" * 60)
        print("Phase 1: Scan & Plan")
        print("=" * 60)

        class_list = self.scan_project()
        self.state.save_class_list(class_list)
        print(f"Scanned: {len(class_list['classes'])} classes found")

        total_methods = sum(
            len(cls.get("methods", [])) for cls in class_list["classes"]
        )
        print(f"Methods to test: {total_methods}")

        test_plan = self.build_test_plan(class_list)
        self.state.save_test_plan(test_plan)

        # Initial progress
        self.state.write_progress_summary(0, [], {"line": 0.0, "branch": 0.0})

        # Print class breakdown
        type_counts = {}
        for cls in class_list["classes"]:
            t = cls["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        print(f"By type: {type_counts}")

        return self.state.get_summary()

    # ==================== Phase 2: Dispatch ====================

    def run_phase2(self) -> Dict[str, Any]:
        """
        Execute Phase 2: Dispatch Subagents (per-class mode).

        Each subagent handles ONE class with ALL its pending methods.
        The subagent iterates until coverage targets are met or all
        branches are exhausted.
        """
        print("=" * 60)
        print("Phase 2: Dispatch Subagents (per-class)")
        print("=" * 60)

        pending_classes = self.state.get_pending_methods_by_class()
        if not pending_classes:
            print("No classes with pending methods. Moving to evaluation.")
            return self.state.get_summary()

        total_pending = sum(
            sum(1 for m in c["class_methods"]
                if m["test_status"] == "pending")
            for c in pending_classes
        )
        print(f"Classes with pending methods: {len(pending_classes)}")
        print(f"Total pending methods: {total_pending}")

        # Select batch (one subagent per class)
        plan = self.state.load_test_plan()
        batch_size = plan.get("batch_size", 5)
        batch = self.dispatcher.get_parallel_batch(
            pending_classes, batch_size=batch_size
        )

        # Prioritize low-coverage classes
        low_cov = self.state.get_low_coverage_methods()
        if low_cov:
            low_cov_classes = set(m["class_name"] for m in low_cov)
            batch_low = [c for c in batch
                        if c["class_name"] in low_cov_classes]
            batch_other = [c for c in batch
                          if c["class_name"] not in low_cov_classes]
            batch = batch_low + batch_other

        print(f"Batch: {len(batch)} classes")
        for i, c in enumerate(batch):
            pending_count = sum(1 for m in c["class_methods"]
                              if m["test_status"] == "pending")
            print(f"  [{i+1}] {c['class_name']} ({c['type']}, "
                  f"{c['complexity']}) — {pending_count} methods")

        batch_class_names = [c["class_name"] for c in batch]
        self.state.set_current_batch(batch_class_names)

        # Build one prompt per class
        prompts = []
        for class_task in batch:
            # Mark class and all its pending methods as in_progress
            self.state.mark_class_in_progress(class_task["class_name"])
            for m in class_task["class_methods"]:
                if m["test_status"] == "pending":
                    self.state.mark_method_in_progress(
                        class_task["class_name"], m["name"])

            attempt = self.dispatcher.retry_count.get(
                class_task["class_name"], 0) + 1
            class_task["attempt"] = attempt
            self.dispatcher.record_attempt(class_task["class_name"])

            prompt = self.dispatcher.build_subagent_prompt(class_task)
            prompts.append({
                "task": class_task,
                "prompt": prompt,
            })

        print(f"\nSubagent prompts ready: {len(prompts)} (one per class)")
        for i, p in enumerate(prompts):
            task = p["task"]
            print(f"  [{i+1}] {task['class_name']} "
                  f"(attempt {task.get('attempt', 1)})")

        return {
            "phase": "generate",
            "batch": batch,
            "prompts": prompts,
            "classes_remaining": len(pending_classes) - len(batch),
        }

    def apply_batch_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply per-class subagent results (each may contain multiple test methods)."""
        print("\nApplying batch results...")

        for r in results:
            class_name = r.get("class_name", "")
            status = r.get("status", "fail")
            class_cov = r.get("class_coverage", {})
            line_cov = class_cov.get("line_coverage", 0)
            branch_cov = class_cov.get("branch_coverage", 0)

            if status == "class_complete":
                # All coverage targets met for this class
                self.state.mark_class_met_targets(
                    class_name, line_cov, branch_cov)
                for tr in r.get("test_results", []):
                    if tr.get("status") == "pass":
                        self.state.mark_method_pass(
                            class_name, tr["method_name"])
                    elif tr.get("status") == "fail":
                        self.state.mark_method_fail(
                            class_name, tr["method_name"],
                            tr.get("error", ""))
                self.dispatcher.reset_retry(class_name)
                print(f"  COMPLETE: {class_name} "
                      f"(L:{line_cov:.1%} B:{branch_cov:.1%}) "
                      f"tests={len(r.get('test_results', []))} "
                      f"iters={r.get('iterations', 0)}")

            elif status == "class_partial":
                # Made progress but targets not met
                self.state.mark_class_exhausted(
                    class_name, line_cov, branch_cov)
                for tr in r.get("test_results", []):
                    if tr.get("status") == "pass":
                        self.state.mark_method_pass(
                            class_name, tr["method_name"])
                    elif tr.get("status") == "fail":
                        self.state.mark_method_fail(
                            class_name, tr["method_name"],
                            tr.get("error", ""))
                self.dispatcher.reset_retry(class_name)
                print(f"  PARTIAL: {class_name} "
                      f"(L:{line_cov:.1%} B:{branch_cov:.1%}) "
                      f"reason={r.get('stop_reason', '?')} "
                      f"uncovered={len(r.get('uncovered_branches', []))}")

            else:  # "fail"
                error = r.get("error", "unknown error")
                self.state.mark_class_failed(class_name, error)
                self.state.reset_class_in_progress(class_name)
                self.state.record_failed_method(
                    class_name, "", f"[CLASS FAIL] {error}")
                print(f"  FAILED: {class_name} — {error[:120]}")

            # Record per-method coverage for tracking
            for tr in r.get("test_results", []):
                if tr.get("status") == "pass":
                    self.state.record_method_coverage(
                        class_name, tr["method_name"],
                        line_cov, branch_cov)

        # Update progress
        iteration = self.state.increment_iteration()
        coverage = self.state.load_coverage_report().get("overall_coverage", {})
        self.state.write_progress_summary(iteration, results, coverage)

        return self.state.get_summary()

    # ==================== Phase 3: Evaluate ====================

    def run_phase3(self) -> Dict[str, Any]:
        """
        Execute Phase 3: Evaluate & Loop.
        Run full mvn test + jacoco:report and check coverage.
        """
        print("=" * 60)
        print("Phase 3: Evaluate & Loop")
        print("=" * 60)

        # Run full test suite
        print("\nRunning full test suite...")
        test_result = self._run_maven_test()

        # Run JaCoCo report
        print("\nGenerating coverage report...")
        coverage_data = self._run_jacoco_report()

        # Save coverage report
        self.state.save_coverage_report({
            "overall_coverage": coverage_data,
            "test_result": test_result,
            "sprint_status": "pass" if self._check_targets(coverage_data) else "rework",
        })

        # Mark evaluation complete for partial evaluation tracking
        self.state.mark_evaluation_complete()

        # Print results
        cov = coverage_data
        print(f"\nCoverage: Line {cov.get('line', 0)*100:.1f}%, "
              f"Branch {cov.get('branch', 0)*100:.1f}%")
        print(f"Tests: {test_result.get('tests_run', 0)} run, "
              f"{test_result.get('failures', 0)} failed, "
              f"{test_result.get('errors', 0)} errors")

        if self._check_targets(coverage_data):
            print("\n*** COVERAGE TARGETS MET! ***")
            return {"phase": "complete", "coverage": coverage_data}
        else:
            print("\nCoverage targets NOT met. Continue testing...")
            return {"phase": "generate", "coverage": coverage_data}

    def _run_maven_test(self) -> Dict[str, Any]:
        """Run mvn test and parse results."""
        try:
            result = subprocess.run(
                [self.MAVEN_BIN, "test"],
                cwd=self.java_project_path,
                capture_output=True,
                text=True,
                timeout=300,
            )
            output = result.stdout + result.stderr

            tests_run = 0
            failures = 0
            errors = 0

            m = re.search(r"Tests run:\s*(\d+).*Failures:\s*(\d+).*Errors:\s*(\d+)",
                         output)
            if m:
                tests_run = int(m.group(1))
                failures = int(m.group(2))
                errors = int(m.group(3))

            return {
                "success": result.returncode == 0,
                "tests_run": tests_run,
                "failures": failures,
                "errors": errors,
                "output_preview": output[-500:],
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "tests_run": 0, "failures": 0, "errors": 0,
                    "error": "Test execution timed out (5 min)"}
        except Exception as e:
            return {"success": False, "tests_run": 0, "failures": 0, "errors": 0,
                    "error": str(e)}

    def _run_jacoco_report(self) -> Dict[str, float]:
        """Run mvn jacoco:report and parse coverage metrics."""
        try:
            subprocess.run(
                [self.MAVEN_BIN, "jacoco:report"],
                cwd=self.java_project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Try to parse the CSV report
            csv_path = os.path.join(
                self.java_project_path,
                "target", "site", "jacoco", "jacoco.csv"
            )
            if os.path.exists(csv_path):
                return self._parse_jacoco_csv(csv_path)

            return {"line": 0.0, "branch": 0.0, "method": 0.0,
                    "note": "jacoco.csv not found"}
        except subprocess.TimeoutExpired:
            return {"line": 0.0, "branch": 0.0, "method": 0.0,
                    "error": "JaCoCo timed out"}
        except Exception as e:
            return {"line": 0.0, "branch": 0.0, "method": 0.0,
                    "error": str(e)}

    def _parse_jacoco_csv(self, csv_path: str) -> Dict[str, float]:
        """Parse JaCoCo CSV report to get overall coverage.

        JaCoCo CSV has one header row then one row per class — no total row.
        We sum all class rows to compute overall coverage.
        """
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) < 2:
            return {"line": 0.0, "branch": 0.0, "method": 0.0}

        header = lines[0].strip().split(",")
        col_map = {h.lower(): i for i, h in enumerate(header)}

        # Sum across all class rows (no total row in JaCoCo CSV)
        totals = {"LINE_MISSED": 0, "LINE_COVERED": 0,
                  "BRANCH_MISSED": 0, "BRANCH_COVERED": 0,
                  "METHOD_MISSED": 0, "METHOD_COVERED": 0}
        per_class = []

        for line in lines[1:]:
            cols = line.strip().split(",")
            if len(cols) < len(header):
                continue

            lm = int(cols[col_map["line_missed"]])
            lc = int(cols[col_map["line_covered"]])
            bm = int(cols[col_map["branch_missed"]])
            bc = int(cols[col_map["branch_covered"]])
            mm = int(cols[col_map["method_missed"]])
            mc = int(cols[col_map["method_covered"]])

            totals["LINE_MISSED"] += lm
            totals["LINE_COVERED"] += lc
            totals["BRANCH_MISSED"] += bm
            totals["BRANCH_COVERED"] += bc
            totals["METHOD_MISSED"] += mm
            totals["METHOD_COVERED"] += mc

            line_total = lm + lc
            branch_total = bm + bc
            per_class.append({
                "class": cols[col_map["class"]],
                "line_coverage": round(lc / line_total, 4) if line_total > 0 else 0.0,
                "branch_coverage": round(bc / branch_total, 4) if branch_total > 0 else 0.0,
            })

        tl = totals
        return {
            "line": tl["LINE_COVERED"] / (tl["LINE_MISSED"] + tl["LINE_COVERED"])
                    if (tl["LINE_MISSED"] + tl["LINE_COVERED"]) > 0 else 0.0,
            "branch": tl["BRANCH_COVERED"] / (tl["BRANCH_MISSED"] + tl["BRANCH_COVERED"])
                      if (tl["BRANCH_MISSED"] + tl["BRANCH_COVERED"]) > 0 else 0.0,
            "method": tl["METHOD_COVERED"] / (tl["METHOD_MISSED"] + tl["METHOD_COVERED"])
                      if (tl["METHOD_MISSED"] + tl["METHOD_COVERED"]) > 0 else 0.0,
            "per_class": per_class,
        }

    def _check_targets(self, coverage: Dict[str, float]) -> bool:
        plan = self.state.load_test_plan()
        targets = plan.get("coverage_target", {"line": 0.70, "branch": 0.60})
        return coverage.get("line", 0) >= targets.get("line", 0.70) and \
               coverage.get("branch", 0) >= targets.get("branch", 0.60)

    def get_low_coverage_classes(self, threshold: float = 0.50) -> List[Dict[str, Any]]:
        """Identify classes with coverage below threshold for prioritization."""
        coverage_data = self.state.load_coverage_report()
        per_class = coverage_data.get("overall_coverage", {}).get("per_class", [])
        low = [c for c in per_class if c.get("line_coverage", 0) < threshold]
        low.sort(key=lambda c: c.get("line_coverage", 0))
        return low

    def get_coverage_gap(self) -> Dict[str, float]:
        """Calculate how far we are from targets."""
        plan = self.state.load_test_plan()
        targets = plan.get("coverage_target", {"line": 0.70, "branch": 0.60})
        current = self.state.load_coverage_report().get("overall_coverage", {})
        return {
            "line_gap": max(0, targets.get("line", 0.70) - current.get("line", 0)),
            "branch_gap": max(0, targets.get("branch", 0.60) - current.get("branch", 0)),
        }

    # ==================== Main Loop ====================

    def run(self, max_iterations: int = 200) -> Dict[str, Any]:
        """
        Run the full orchestration loop.

        Returns when coverage targets met or max_iterations reached.
        """
        print("\n" + "=" * 60)
        print("UT Generation Orchestrator")
        print(f"Project: {self.java_project_path}")
        print("=" * 60 + "\n")

        for iteration in range(max_iterations):
            phase = self.state.detect_phase()
            summary = self.state.get_summary()

            print(f"\n--- Iteration {iteration + 1} | Phase: {phase} ---")
            m = summary["methods"]
            c = summary["coverage"]
            print(f"Methods: {m['pass']}/{m['total']} pass, "
                  f"{m['pending']} pending, {m['fail']} fail")
            print(f"Coverage: Line {c['line']*100:.1f}%, "
                  f"Branch {c['branch']*100:.1f}%")

            if phase == "init":
                self.run_phase1()
                print("\n[Orchestrator] Phase 1 complete. Ready to dispatch subagents.")
                print("[Orchestrator] Use /ralph-loop or re-run to continue with Phase 2.")
                break

            elif phase == "generate":
                batch_info = self.run_phase2()
                prompts = batch_info.get("prompts", [])

                if not prompts:
                    print("[Orchestrator] No prompts to dispatch. Moving to evaluate.")
                    continue

                # In actual Claude Code usage, this is where the orchestrator
                # uses the Agent tool to dispatch subagents in parallel.
                #
                # For automated testing, we print the prompts so the calling
                # Claude Code session can use Agent tool on them.
                print(f"\n[Orchestrator] {len(prompts)} subagent prompts ready.")
                print("[Orchestrator] Dispatch these using the Claude Code Agent tool.")
                print("[Orchestrator] Then provide results back to apply_batch_results().")
                break

            elif phase == "evaluate":
                result = self.run_phase3()
                if result.get("phase") == "complete":
                    print("\n*** ALL DONE! Coverage targets met. ***")
                    return {"status": "complete", "summary": self.state.get_summary()}
                # else: loop back to generate

            elif phase == "complete":
                print("\n*** ALL DONE! Coverage targets met. ***")
                return {"status": "complete", "summary": self.state.get_summary()}

        return {"status": "in_progress", "summary": self.state.get_summary()}

    def run_iteration(self) -> Dict[str, Any]:
        """
        Run a single iteration (called by external loop like Ralph Loop).
        Returns result with next action hint.
        """
        phase = self.state.detect_phase()

        if phase == "init":
            return self.run_phase1()

        elif phase == "generate":
            return self.run_phase2()

        elif phase == "evaluate":
            return self.run_phase3()

        elif phase == "complete":
            return {"phase": "complete", "summary": self.state.get_summary()}

        return {"phase": phase, "summary": self.state.get_summary()}

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
from typing import Any, Dict, List, Optional, Tuple

from .state_manager import StateManager
from .subagent_dispatch import SubagentDispatch


class Orchestrator:
    """Core orchestrator for the UT generation system."""

    MAVEN_BIN = "/home/twinkle/app/maven/bin/mvn"

    # Priority by class type (lower = higher priority)
    TYPE_PRIORITY = {
        "entity": 1,
        "utils": 2,
        "controller": 3,
        "service": 4,
        "mapper": 5,
        "other": 6,
    }

    # Classes to skip (not suitable for unit testing)
    SKIP_PATTERNS = [
        r".*Application$",
        r".*Config$",
        r".*Configuration$",
        r".*Constants$",
        r".*Exception$",
        r".*Interceptor$",
    ]

    def __init__(self, project_root: str, java_project: str = "dianping"):
        self.project_root = project_root
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
        if "mapper" in pkg_lower or "dao" in pkg_lower or "repository" in pkg_lower:
            return "mapper"
        if "entity" in pkg_lower or "model" in pkg_lower or "domain" in pkg_lower or "dto" in pkg_lower:
            return "entity"
        if "utils" in pkg_lower or "util" in pkg_lower or "helper" in pkg_lower:
            return "utils"
        if "config" in pkg_lower:
            return "other"
        return "other"

    def extract_methods(self, filepath: str) -> List[Dict[str, str]]:
        """Extract public method signatures from a Java source file."""
        methods = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return methods

        # Match public methods (simplified regex - handles common patterns)
        pattern = re.compile(
            r'^\s*public\s+(?:static\s+)?(?:final\s+)?'
            r'(?:@\w+\s*)*'  # annotations on separate lines before method
            r'(?:<[^>]+>\s*)?'  # generic return type
            r'(\w+(?:\[\])?(?:<[^>]+>)?)\s+'  # return type
            r'(\w+)\s*'  # method name
            r'\((.*?)\)',  # parameters
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3)

            # Skip constructors (method name same as class)
            # We detect this by checking if the line has no return type before the name
            line_start = max(0, match.start() - 200)
            line_context = content[line_start:match.start()]
            if f"class " in line_context.split("\n")[-1] if "\n" in line_context else False:
                continue

            # Determine complexity
            method_body_start = match.end()
            complexity = self._estimate_complexity(content, method_body_start, method_name)

            test_method_name = self._generate_test_method_name(method_name, return_type)

            methods.append({
                "name": method_name,
                "signature": f"public {return_type} {method_name}({params})",
                "test_status": "pending",
                "test_method": test_method_name,
                "complexity": complexity,
            })

        return methods

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
        Execute Phase 2: Dispatch Subagents.
        Builds prompts for the next batch of pending methods.

        In actual Claude Code usage, the orchestrator (this Claude Code session)
        would use the Agent tool to dispatch these subagents.

        This method prepares the batch and returns the prompts that
        the orchestrator should dispatch.
        """
        print("=" * 60)
        print("Phase 2: Dispatch Subagents")
        print("=" * 60)

        pending = self.state.get_pending_methods()
        if not pending:
            print("No pending methods. Moving to evaluation.")
            return self.state.get_summary()

        print(f"Pending methods: {len(pending)}")

        # Select batch (different classes only)
        batch = self.dispatcher.get_parallel_batch(
            pending, batch_size=self.state.load_test_plan().get("batch_size", 5)
        )
        print(f"Batch size: {len(batch)}")

        batch_class_names = list(set(m["class_name"] for m in batch))
        self.state.set_current_batch(batch_class_names)

        # Build prompts for each subagent
        prompts = []
        for task in batch:
            self.state.mark_method_in_progress(task["class_name"], task["method_name"])
            prompt = self.dispatcher.build_subagent_prompt(task)
            prompts.append({
                "task": task,
                "prompt": prompt,
            })

        print("Subagent prompts ready:")
        for i, p in enumerate(prompts):
            task = p["task"]
            print(f"  [{i+1}] {task['class_name']}.{task['method_name']} "
                  f"→ {task['test_method']}")

        return {
            "phase": "generate",
            "batch": batch,
            "prompts": prompts,
            "pending_remaining": len(pending) - len(batch),
        }

    def apply_batch_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply subagent results to state files."""
        print("\nApplying batch results...")

        for r in results:
            class_name = r.get("class_name", "")
            method_name = r.get("method_name", "")
            status = r.get("status", "fail")

            if status == "pass":
                self.state.mark_method_pass(class_name, method_name)
            else:
                error = r.get("error", "unknown")
                self.state.mark_method_fail(class_name, method_name, error)
                self.state.record_failed_method(class_name, method_name, error)

            print(f"  {status.upper()}: {class_name}.{method_name}")

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
        """Parse JaCoCo CSV report to get overall coverage."""
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) < 2:
            return {"line": 0.0, "branch": 0.0, "method": 0.0}

        # The last line is the total
        header = lines[0].strip().split(",")
        total = lines[-1].strip().split(",")

        # Find column indices
        col_map = {h.lower(): i for i, h in enumerate(header)}

        def get_val(prefix):
            missed = int(total[col_map.get(f"{prefix}_missed", 0)])
            covered = int(total[col_map.get(f"{prefix}_covered", 0)])
            total_count = missed + covered
            return covered / total_count if total_count > 0 else 0.0

        return {
            "line": get_val("instruction"),
            "branch": get_val("branch"),
            "method": get_val("method"),
        }

    def _check_targets(self, coverage: Dict[str, float]) -> bool:
        return coverage.get("line", 0) >= 0.70 and coverage.get("branch", 0) >= 0.60

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

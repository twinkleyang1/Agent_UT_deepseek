"""
Subagent Dispatch - builds prompts and tracks subagent results.

Each subagent is dispatched via Claude Code's Agent tool to write
one JUnit 5 test method, run it, and return the result.
"""

import json
import os
from typing import Any, Dict, List, Optional


class SubagentDispatch:
    """Builds subagent prompts and tracks dispatch results."""

    MAVEN_BIN = "/home/twinkle/app/maven/bin/mvn"
    RULES_DIR = "Rule"
    SUBAGENT_PROMPT_TEMPLATE = "prompts/SUBAGENT_UT_PROMPT.md"

    def __init__(self, project_root: str, java_project: str):
        self.project_root = project_root
        self.java_project = java_project  # e.g. dianping

    def build_subagent_prompt(self, task: Dict[str, str]) -> str:
        """
        Build a precise subagent prompt for writing one test method.

        Args:
            task: Dict with keys:
                - class_name, package, class_path, test_file
                - method_name, signature, test_method, complexity
        """
        class_name = task["class_name"]
        method_name = task["method_name"]
        signature = task["signature"]
        test_method = task["test_method"]
        test_file = task["test_file"]
        class_path = task["class_path"]
        pkg = task["package"]

        java_project_path = os.path.join(self.project_root, self.java_project)
        rules_path = os.path.join(self.project_root, self.RULES_DIR,
                                  "Java_UT_Testing_Rules.md")

        prompt = f"""You are a Java UT test-writing specialist. Your job is to write ONE test method.

## Target
- Class: {pkg}.{class_name}
- Method: {method_name}
- Signature: {signature}
- Source file: {java_project_path}/{class_path}
- Test file: {java_project_path}/{test_file}
- Test method name: {test_method}

## Task
1. Read the source file at `{java_project_path}/{class_path}` and understand the `{method_name}` method
2. Design a single test case following AAA (Arrange-Act-Assert) pattern
3. If the test file does not exist, create it with the proper package, imports, class declaration, and @ExtendWith(MockitoExtension.class)
4. If the test file already exists, append the new test method to the existing class
5. Run the test: cd {java_project_path} && {self.MAVEN_BIN} test -Dtest={class_name}Test#{test_method}
6. Return the result as JSON

## Test Writing Rules
Refer to: {rules_path}

Key rules:
- JUnit 5 + Mockito (@ExtendWith(MockitoExtension.class))
- Method naming: should[Expected]When[Condition]
- AAA pattern: // Arrange, // Act, // Assert
- Mock ALL external dependencies (Redis, MyBatis, Database) with @Mock
- Use @InjectMocks for the class under test
- One test = one behavior (do NOT write multiple test methods)

## Return Format
You MUST end your response with exactly this JSON block:
```json
{{
  "status": "pass|fail",
  "class_name": "{class_name}",
  "method_name": "{method_name}",
  "test_method": "{test_method}",
  "test_file": "{test_file}",
  "error": "error message if failed, null if passed",
  "duration_ms": 0
}}
```
"""
        return prompt

    def build_batch_summary(self, results: List[Dict[str, Any]]) -> str:
        """Build a summary of batch results for the orchestrator."""
        passed = [r for r in results if r.get("status") == "pass"]
        failed = [r for r in results if r.get("status") != "pass"]

        lines = [
            f"## Batch Summary",
            f"- Total: {len(results)}",
            f"- Passed: {len(passed)}",
            f"- Failed: {len(failed)}",
        ]

        if passed:
            lines.append("\n### Passed:")
            for r in passed:
                lines.append(f"  ✓ {r.get('class_name')}.{r.get('method_name')} "
                             f"→ {r.get('test_method')} ({r.get('duration_ms', 0)}ms)")

        if failed:
            lines.append("\n### Failed:")
            for r in failed:
                error = r.get("error", "unknown error")
                lines.append(f"  ✗ {r.get('class_name')}.{r.get('method_name')} "
                             f"→ {error[:120]}")

        return "\n".join(lines)

    def parse_subagent_result(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse the JSON result from a subagent's response."""
        try:
            # Find the JSON block in the response
            start = response.rfind("```json")
            if start == -1:
                start = response.rfind("{")
                end = response.rfind("}") + 1
            else:
                start = response.find("{", start)
                end = response.find("```", start)
                if end == -1:
                    end = response.rfind("}") + 1

            if start == -1:
                return None

            json_str = response[start:end].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            return None

    def get_parallel_batch(self, pending: List[Dict[str, Any]],
                           batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        Select a batch of methods that can run in parallel.
        Ensures no two methods from the same class are in the same batch.
        """
        batch = []
        used_classes = set()

        for method in pending:
            cls = method["class_name"]
            if cls in used_classes:
                continue
            batch.append(method)
            used_classes.add(cls)
            if len(batch) >= batch_size:
                break

        return batch

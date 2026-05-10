"""
Subagent Dispatch - builds per-class prompts with iterative coverage loop.

Each subagent is dispatched via Claude Code's Agent tool for ONE class.
The subagent writes tests iteratively until class coverage targets are met
or all branches are exhausted.
"""

import json
import os
from typing import Any, Dict, List, Optional


class SubagentDispatch:
    """Builds subagent prompts and tracks dispatch results (per-class mode)."""

    MAVEN_BIN = "/home/twinkle/app/maven/bin/mvn"
    RULES_DIR = "Rule"
    SUBAGENT_PROMPT_TEMPLATE = "prompts/SUBAGENT_UT_PROMPT.md"
    MAX_RETRIES = 3
    MAX_ITERATIONS = 10  # max iterations per subagent coverage loop
    COVERAGE_TARGET_LINE = 0.70
    COVERAGE_TARGET_BRANCH = 0.60

    def __init__(self, project_root: str, java_project: str):
        self.project_root = project_root
        self.java_project = java_project
        self.retry_count: Dict[str, int] = {}

    # ==================== Retry Tracking (per-class) ====================

    def can_retry(self, class_name: str) -> bool:
        return self.retry_count.get(class_name, 0) < self.MAX_RETRIES

    def record_attempt(self, class_name: str) -> int:
        self.retry_count[class_name] = self.retry_count.get(class_name, 0) + 1
        return self.retry_count[class_name]

    def reset_retry(self, class_name: str) -> None:
        self.retry_count.pop(class_name, None)

    # ==================== Prompt Building ====================

    def build_subagent_prompt(self, task: Dict[str, Any]) -> str:
        """
        Build a per-class subagent prompt with iterative coverage loop.

        Args:
            task: Dict with class-level keys:
                - class_name, package, class_path, test_file, type, complexity
                - class_methods: list of method dicts (name, signature, test_method,
                  complexity, test_status)
                - attempt: retry attempt number
        """
        class_name = task["class_name"]
        pkg = task["package"]
        class_path = task["class_path"]
        test_file = task["test_file"]
        class_type = task.get("type", "other")
        complexity = task.get("complexity", "medium")
        attempt = task.get("attempt", 1)
        class_methods = task.get("class_methods", [])

        java_project_path = os.path.join(self.project_root, self.java_project)
        rules_path = os.path.join(self.project_root, self.RULES_DIR,
                                  "Java_UT_Testing_Rules.md")
        prompt_template_path = os.path.join(self.project_root,
                                            self.SUBAGENT_PROMPT_TEMPLATE)

        # Build method inventory table
        method_table = self._build_method_table(class_methods)

        # Build mock guidance
        mock_guidance = self._build_mock_guidance(class_type, pkg, class_name)

        # Build branch guidance for class context
        pending_count = sum(1 for m in class_methods
                           if m.get("test_status") == "pending")
        branch_guidance = self._build_branch_guidance(complexity, pending_count)

        retry_note = ""
        if attempt > 1:
            retry_note = f"""## RETRY ATTEMPT {attempt}/{self.MAX_RETRIES}
Previous attempt for this class failed. Review the error and fix accordingly.

"""

        prompt = f"""You are a Java UT test-writing specialist. Your job is to write tests for ONE class until coverage targets are met or all branches are exhausted.

## Target Class
- Class: {pkg}.{class_name} ({class_type})
- Source file: {java_project_path}/{class_path}
- Test file: {java_project_path}/{test_file}
- Complexity: {complexity}
- Coverage targets: Line >= {int(self.COVERAGE_TARGET_LINE*100)}%, Branch >= {int(self.COVERAGE_TARGET_BRANCH*100)}%

{retry_note}
## Method Inventory
{method_table}

Methods marked "pass" already have working tests — do NOT duplicate them.
Methods marked "pending" need tests.
Methods marked "fail" need fixed tests.

## Coverage Iteration Loop (CRITICAL)

You MUST iterate until one of these STOP conditions is met:
  **STOP-A**: {class_name} line_coverage >= 70% AND branch_coverage >= 60%
  **STOP-B**: No uncovered branches remain for ANY pending/failed method
  **STOP-C**: You have completed {self.MAX_ITERATIONS} iterations

### Initial Setup (Iteration 0)
1. Read the source file to understand ALL methods, their branches, and dependencies
2. Read the existing test file (if any) to see existing tests
3. Run baseline: cd {java_project_path} && {self.MAVEN_BIN} test -Dtest={class_name}Test
4. Run coverage: cd {java_project_path} && {self.MAVEN_BIN} jacoco:report
5. Parse `target/site/jacoco/jacoco.csv` — find row for `{class_name}`, note baseline line_coverage and branch_coverage

### Each Iteration
1. Identify uncovered branches from the LATEST jacoco.csv metrics
2. Pick the highest-priority uncovered branch and write ONE test for it
3. Run: cd {java_project_path} && {self.MAVEN_BIN} test -Dtest={class_name}Test#testMethod
4. If test FAILS: fix the test and re-run (same iteration — don't advance)
5. After test passes: cd {java_project_path} && {self.MAVEN_BIN} jacoco:report
6. Parse `target/site/jacoco/jacoco.csv` for row `{class_name}`:
   - line_coverage = LINE_COVERED / (LINE_MISSED + LINE_COVERED)
   - branch_coverage = BRANCH_COVERED / (BRANCH_MISSED + BRANCH_COVERED)
   - If BRANCH_MISSED + BRANCH_COVERED == 0, branch_coverage = 0
7. Check STOP conditions — if none met, increment iteration and continue

### Branch Prioritization
1. Complex methods first (most uncovered branches)
2. Medium methods next
3. Simple methods last
4. Within a method: error/null paths first, then happy paths

### Constraints
- Max {self.MAX_ITERATIONS} iterations total
- Write at most 2 tests per iteration
- Do NOT modify source code — only add/modify test file
- If the test file does not exist, create it with proper structure
- If the test file exists, append new @Test methods
- After EACH test pass, run jacoco:report and parse coverage

{mock_guidance}

{branch_guidance}

## Test Writing Rules
Refer to: {rules_path} and {prompt_template_path}

Key rules:
- JUnit 5 + Mockito (@ExtendWith(MockitoExtension.class))
- Add @MockitoSettings(strictness = Strictness.LENIENT) to class level
- Method naming: should[Expected]When[Condition]
- AAA pattern: // Arrange, // Act, // Assert
- Mock ALL external dependencies (Redis, MyBatis, Database, MQ) with @Mock
- Use @InjectMocks for the class under test
- One test = one behavior = one branch
- For MyBatis-Plus: chain calls delegate to baseMapper — mock the baseMapper
- For Redis: mock StringRedisTemplate + each ops type
- For ThreadLocal: set directly + cleanup in @AfterEach

## Return Format
You MUST end your response with exactly this JSON block:
```json
{{
  "status": "class_complete|class_partial|fail",
  "class_name": "{class_name}",
  "class_coverage": {{
    "line_coverage": 0.0,
    "branch_coverage": 0.0
  }},
  "stop_reason": "targets_met|branches_exhausted|max_iterations|compilation_error",
  "test_results": [
    {{
      "status": "pass",
      "method_name": "methodName",
      "test_method": "shouldXxxWhenYyy",
      "branches_covered": ["branch description"],
      "duration_ms": 0
    }}
  ],
  "iterations": 0,
  "uncovered_branches": [],
  "error": null,
  "total_duration_ms": 0
}}
```
- `status`: "class_complete" (targets met), "class_partial" (progress made but not met), "fail" (fatal error)
- `stop_reason`: why the loop stopped
- `test_results`: ALL tests written in this dispatch (can be empty if fail)
- `uncovered_branches`: remaining uncovered branch descriptions (for class_partial)
- `error`: set only if status=fail
"""
        return prompt

    def _build_method_table(self, class_methods: List[Dict[str, Any]]) -> str:
        """Build a markdown table of methods in the class."""
        lines = [
            "| # | Method | Signature | Complexity | Status | Suggested Test |",
            "|---|--------|-----------|------------|--------|----------------|",
        ]
        for i, m in enumerate(class_methods):
            lines.append(
                f"| {i+1} | {m['name']} | {m.get('signature', '')} "
                f"| {m.get('complexity', 'medium')} "
                f"| {m.get('test_status', 'pending')} "
                f"| {m.get('test_method', '')} |"
            )
        return "\n".join(lines)

    def _build_mock_guidance(self, class_type: str, pkg: str,
                             class_name: str) -> str:
        """Build type-specific mock guidance based on class type."""
        guidance_parts = ["## Mock Strategy for This Class Type\n"]

        if class_type == "service":
            guidance_parts.append(
                "**Service class** - Typical dependencies:\n"
                "- MyBatis-Plus Mapper: `@Mock Mapper` + mock `baseMapper.selectOne/selectList/selectPage/update/updateById/insert`\n"
                "- Redis: `@Mock StringRedisTemplate` + "
                "mock `opsForValue/opsForSet/opsForZSet/opsForHash/opsForList/opsForGeo` → "
                "`@Mock ValueOperations/SetOperations/ZSetOperations/HashOperations/ListOperations/GeoOperations`\n"
                "- Other services: `@Mock ISomeService`\n"
                "- Redisson: `@Mock RedissonClient` + `@Mock RLock`\n"
                "- MyBatis-Plus chain calls: query().eq().one() → mock baseMapper.selectOne(); "
                "update().setSql().eq().update() → mock baseMapper.update(null, wrapper)\n"
                "- Add `@MockitoSettings(strictness = Strictness.LENIENT)` to class level"
            )
        elif class_type == "controller":
            guidance_parts.append(
                "**Controller class** - Use `@InjectMocks` with `@Mock` services (NOT @WebMvcTest):\n"
                "- `@Mock ISomeService` for each service dependency\n"
                "- `@InjectMocks SomeController`\n"
                "- Call controller methods directly (no MockMvc)\n"
                "- Assert on returned Result object: `assertTrue(result.getSuccess())`, "
                "`assertEquals(200, result.getCode())`\n"
                "- No Spring context needed — pure Mockito test"
            )
        elif class_type == "config":
            guidance_parts.append(
                "**Config class** - Test @Bean factory methods:\n"
                "- Create the config object directly: `new SomeConfig()`\n"
                "- Call the @Bean method directly\n"
                "- Assert the returned bean is not null and properly configured\n"
                "- If the config method takes parameters, use `@Mock` for dependencies and "
                "`@InjectMocks` for the config class"
            )
        elif class_type == "interceptor":
            guidance_parts.append(
                "**Interceptor class** - Test preHandle/postHandle:\n"
                "- Create interceptor with `new` (pass mocked dependencies to constructor)\n"
                "- Use `MockHttpServletRequest` and `MockHttpServletResponse` from spring-test\n"
                "- Set headers with `request.addHeader(\"authorization\", \"token\")`\n"
                "- ThreadLocal cleanup in `@AfterEach`: `UserHolder.removeUser()`\n"
                "- Test both branches: token present/absent, user exists/not-exists"
            )
        elif class_type == "utils":
            guidance_parts.append(
                "**Utility class** - May have static methods:\n"
                "- If the class has only static methods, call them directly (no @InjectMocks)\n"
                "- If it uses external dependencies, use `@InjectMocks` with `@Mock` deps\n"
                "- For Redis-based utils: mock StringRedisTemplate + ops"
            )
        elif class_type == "mapper":
            guidance_parts.append(
                "**Mapper class** - MyBatis interface:\n"
                "- If the mapper has custom SQL methods, test them\n"
                "- Mock the mapper's dependencies if any"
            )
        else:
            guidance_parts.append(
                "**Other class** - Assess dependencies and mock accordingly:\n"
                "- Mock Redis, database, and external services\n"
                "- Use @Mock + @InjectMocks pattern"
            )

        return "\n".join(guidance_parts)

    def _build_branch_guidance(self, complexity: str,
                                method_count: int) -> str:
        """Build branch coverage guidance for class context."""
        if complexity == "complex":
            return (
                "## Class Coverage Strategy\n"
                f"COMPLEX class with {method_count} pending methods — many branches to cover.\n"
                "Work methodically: complex methods first, then medium, then simple.\n"
                "After each test, re-check jacoco.csv for uncovered branches.\n"
                "DO NOT write tests for branches already covered."
            )
        elif complexity == "medium":
            return (
                "## Class Coverage Strategy\n"
                f"{method_count} pending methods with moderate branching.\n"
                "Write tests method-by-method, checking coverage after each pass.\n"
                "Prioritize methods with the most branching."
            )
        else:
            return (
                "## Class Coverage Strategy\n"
                f"{method_count} pending methods, relatively simple.\n"
                "Cover main paths first, then edge cases (null input, empty result)."
            )

    # ==================== Batch Selection ====================

    def get_parallel_batch(self, pending_classes: List[Dict[str, Any]],
                           batch_size: int = 5,
                           prioritize_complex: bool = True) -> List[Dict[str, Any]]:
        """
        Select a batch of classes for parallel subagent dispatch.

        Args:
            pending_classes: List of class dicts (from get_pending_methods_by_class)
            batch_size: Max classes per batch
            prioritize_complex: If True, complex classes first
        """
        if prioritize_complex:
            complexity_order = {"complex": 0, "medium": 1, "simple": 2}
            pending_classes = sorted(
                pending_classes,
                key=lambda c: (
                    complexity_order.get(c.get("complexity", "medium"), 3),
                    -sum(1 for m in c.get("class_methods", [])
                         if m.get("test_status") == "pending"),
                    c.get("priority", 5),
                )
            )
        return pending_classes[:batch_size]

    def get_retry_batch(self, failed_methods: List[Dict[str, Any]],
                        batch_size: int = 3) -> List[Dict[str, Any]]:
        """Select classes to retry from failed list."""
        retry_candidates = []
        for m in failed_methods:
            class_name = m.get("class_name", m.get("class", ""))
            if self.can_retry(class_name):
                m_copy = dict(m)
                m_copy["class_name"] = class_name
                m_copy["attempt"] = self.retry_count.get(class_name, 0) + 1
                retry_candidates.append(m_copy)
        return retry_candidates[:batch_size]

    # ==================== Result Handling ====================

    def build_batch_summary(self, results: List[Dict[str, Any]]) -> str:
        """Build a summary of per-class batch results."""
        complete = [r for r in results if r.get("status") == "class_complete"]
        partial = [r for r in results if r.get("status") == "class_partial"]
        failed = [r for r in results if r.get("status") == "fail"]

        lines = [
            "## Batch Summary",
            f"- Classes: {len(results)} total",
            f"- Complete (targets met): {len(complete)}",
            f"- Partial (exhausted): {len(partial)}",
            f"- Failed: {len(failed)}",
        ]

        for r in complete:
            cov = r.get("class_coverage", {})
            lines.append(
                f"  + {r.get('class_name')} "
                f"(L:{cov.get('line_coverage', 0)*100:.0f}% "
                f"B:{cov.get('branch_coverage', 0)*100:.0f}%) "
                f"tests={len(r.get('test_results', []))} "
                f"iters={r.get('iterations', 0)}"
            )

        for r in partial:
            cov = r.get("class_coverage", {})
            lines.append(
                f"  ~ {r.get('class_name')} "
                f"(L:{cov.get('line_coverage', 0)*100:.0f}% "
                f"B:{cov.get('branch_coverage', 0)*100:.0f}%) "
                f"reason={r.get('stop_reason', '?')}"
            )

        for r in failed:
            lines.append(
                f"  x {r.get('class_name')} "
                f"error={r.get('error', 'unknown')[:120]}"
            )

        return "\n".join(lines)

    def parse_subagent_result(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse the JSON result from a subagent's response."""
        try:
            start = response.rfind("```json")
            if start == -1:
                start = response.rfind('{"status"')
                if start == -1:
                    start = response.rfind('{\n  "status"')
                end = response.rfind("}") + 1 if start != -1 else -1
            else:
                start = response.find("{", start)
                end = response.find("```", start)
                if end == -1:
                    end = response.rfind("}") + 1

            if start == -1 or end <= start:
                return None

            json_str = response[start:end].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            return None

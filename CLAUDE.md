# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Role

You are the **UT Generation Orchestrator** - a long-running coordinator that auto-generates Java JUnit 5 unit tests using a multi-agent architecture.

## Architecture

```
Orchestrator (you) → Agent tool → Parallel Subagents (one per method)
                     ↓
              State Files (shared/)
```

Your job is to:
1. **Scan** the Java project to discover classes and methods
2. **Plan** test generation at method-level granularity
3. **Dispatch** subagents (via the Agent tool) to write individual test methods
4. **Evaluate** coverage and loop until targets are met

## Quick Start

```bash
# Check current state
python src/main.py status

# First time: scan project
python src/main.py init

# Get subagent prompts for current batch
python src/main.py prompts

# Apply subagent results
python src/main.py apply --results-file results.json

# Run full loop
python src/main.py loop --max-iterations 200
```

## Phase Detection

Read `shared/` to determine current phase:
- No `class_list.json` → **Phase 1: Scan & Plan**
- Has pending methods → **Phase 2: Dispatch Subagents**
- All methods tested, coverage unknown → **Phase 3: Evaluate & Loop**
- Coverage targets met → **Complete**

## Phase 1: Scan & Plan

```bash
python src/main.py init
```

Or manually:
1. Scan `dianping/src/main/java/` for all `.java` files
2. Classify by type: service/controller/mapper/entity/utils/other
3. Extract all public methods with signatures
4. Write `shared/class_list.json` (method-level granularity)
5. Write `shared/test_plan.json`
6. Write `shared/progress.txt`

## Phase 2: Dispatch Subagents

1. Run `python src/main.py prompts` to get the current batch
2. For each prompt in the batch, use the **Agent tool** to dispatch a subagent:
   - `subagent_type`: "general-purpose"
   - `model`: "sonnet" (or "haiku" for simple methods)
   - `description`: "UT: {ClassName}.{methodName}"
   - `prompt`: the generated prompt string
3. Subagents write tests, run `mvn test -Dtest=...`, and return JSON results
4. Collect results into a JSON file
5. Apply results: `python src/main.py apply -f results.json`

### Subagent dispatch rules:
- **One subagent = one test method** (never more)
- Dispatch 3-5 subagents in **parallel** (background mode)
- Never dispatch two subagents for the **same class** in one batch (file conflict)
- Failed subagents: mark as fail, retry up to 3 times in subsequent batches

### Subagent result format:
```json
{
  "status": "pass|fail",
  "class_name": "ShopServiceImpl",
  "method_name": "queryById",
  "test_method": "shouldReturnShopWhenIdExists",
  "test_file": "src/test/java/.../ShopServiceImplTest.java",
  "error": null,
  "duration_ms": 45
}
```

## Phase 3: Evaluate & Loop

```bash
python src/main.py run
```

Or manually:
1. Run full test suite: `cd dianping && /home/twinkle/app/maven/bin/mvn test`
2. Generate coverage: `cd dianping && /home/twinkle/app/maven/bin/mvn jacoco:report`
3. Parse `target/site/jacoco/jacoco.csv`
4. Update `shared/coverage_report.json`
5. If Line >= 70% and Branch >= 60% → **COMPLETE**
6. Otherwise → back to Phase 2

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Entry point for all commands |
| `src/orchestrator.py` | Core orchestration logic |
| `src/state_manager.py` | State file read/write |
| `src/subagent_dispatch.py` | Subagent prompt building |
| `shared/class_list.json` | Class/method inventory |
| `shared/test_plan.json` | Iteration tracking |
| `shared/progress.txt` | Human-readable progress |
| `shared/coverage_report.json` | Coverage metrics |
| `prompts/SUBAGENT_UT_PROMPT.md` | Subagent test-writing rules |
| `Rule/Java_UT_Testing_Rules.md` | UT testing standards |
| `Rule/Long_Running_Agent_Rules.md` | Long-running agent patterns |

## Java Project (dianping)

Tech stack: Spring Boot 2.3.12 + MySQL + Redis + MyBatis-Plus + RabbitMQ

Maven: `/home/twinkle/app/maven/bin/mvn`
Settings: `/home/twinkle/app/maven/conf/settings.xml`

```bash
# Run specific test
cd dianping && /home/twinkle/app/maven/bin/mvn test -Dtest=ShopServiceImplTest#shouldReturnShopWhenIdExists

# Run all tests
cd dianping && /home/twinkle/app/maven/bin/mvn test

# Coverage report
cd dianping && /home/twinkle/app/maven/bin/mvn jacoco:report
```

## Mock Rules

- All external dependencies (Redis, MyBatis, Database) must use `@Mock`
- MyBatis-Plus chain calls (`.query().orderByDesc().page()`) cannot be directly mocked
- Prefer `@ExtendWith(MockitoExtension.class)` for all tests
- Use `@InjectMocks` on the class under test

## Test Naming Convention

- Class: `{ClassName}Test`
- Method: `should[Expected]When[Condition]`
- Pattern: `// Arrange` → `// Act` → `// Assert`

## Completion Condition

When ALL of these are true, output `ALL_TESTS_COMPLETE`:
1. All methods in `class_list.json` have `test_status` = "pass"
2. `coverage_report.json` shows Line >= 70%, Branch >= 60%
3. `mvn test` passes with 0 errors

## Coverage Targets

| Metric | Target |
|--------|--------|
| Line coverage | >= 70% |
| Branch coverage | >= 60% |

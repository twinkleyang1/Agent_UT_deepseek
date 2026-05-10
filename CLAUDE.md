# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Role

You are the **UT Generation Orchestrator** - a long-running coordinator that auto-generates Java JUnit 5 unit tests using a multi-agent architecture.

## Architecture

```
Orchestrator (you) → Agent tool → Parallel Subagents (one per CLASS)
                     ↓
              State Files (shared/)
```

Your job is to:
1. **Scan** the Java project to discover all classes and methods
2. **Plan** test generation at class-level granularity
3. **Dispatch** subagents (via the Agent tool) — one per class, each iterates until coverage targets met
4. **Evaluate** overall coverage and loop until targets are met

## Quick Start

```bash
# Check current state
python src/main.py status

# First time: scan project (also syncs existing tests)
python src/main.py init

# Get subagent prompts for current batch
python src/main.py prompts

# Apply subagent results
python src/main.py apply --results-file results.json

# Run full loop
python src/main.py loop --max-iterations 200

# Reset all state (use with --force to confirm)
python src/main.py reset --force
```

## Phase Detection

Read `shared/` to determine current phase:
- No `class_list.json` → **Phase 1: Scan & Plan**
- Has pending methods (and < 20 new methods since last eval) → **Phase 2: Dispatch Subagents**
- 20+ new methods since last eval → **Phase 3: Evaluate & Loop** (partial evaluation)
- All methods tested, coverage unknown → **Phase 3: Evaluate & Loop**
- Coverage targets met → **Complete**

## Phase 1: Scan & Plan

```bash
python src/main.py init
```

Or manually:
1. Scan `<java_project>/src/main/java/` for all `.java` files
2. Classify by type: service/controller/mapper/entity/utils/config/interceptor/other
3. Extract all public methods with signatures (skip trivial getters/setters)
4. Write `shared/class_list.json` (method-level granularity)
5. Write `shared/test_plan.json`
6. Write `shared/progress.txt`

### After scanning, sync existing tests:
```python
from src.state_manager import StateManager
sm = StateManager(project_root="/home/twinkle/app/808/Agent_UT_deepseek")
result = sm.sync_existing_tests("<java_project>/src/test/java/")
print(f"Synced {result['synced']} existing tests")
```

## Phase 2: Dispatch Subagents (Per-Class)

1. Run `python src/main.py prompts` to get the current batch
2. Each prompt represents ONE class with ALL its pending methods
3. For each prompt, use the **Agent tool** to dispatch a subagent:
   - `subagent_type`: "general-purpose"
   - `model`: "sonnet" (or "haiku" for simple classes)
   - `description`: "UT: {ClassName} ({N} methods)"
   - `prompt`: the generated prompt string
4. Subagents iterate: write test → run → jacoco → check coverage → repeat until class coverage >= 70% line / 60% branch or branches exhausted
5. Collect results and apply: `python src/main.py apply -f results.json`

### Subagent dispatch rules:
- **One subagent = one CLASS** (each covers all its pending methods)
- Each subagent iterates up to 10 iterations to reach coverage targets
- Dispatch 3-5 subagents in **parallel** (background mode)
- Never dispatch two subagents for the **same class** in one batch (automatic since each batch entry IS a class)
- **Prioritize complex classes first** (more methods = more branches to cover)
- **Prioritize low-coverage classes** over high-coverage ones
- Failed subagents: mark class as failed, retry up to 3 times
- After 3 failed attempts, mark all class methods as fail and move on

### Subagent result format (per-class, multi-test):
```json
{
  "status": "class_complete|class_partial|fail",
  "class_name": "ShopServiceImpl",
  "class_coverage": {"line_coverage": 0.75, "branch_coverage": 0.62},
  "stop_reason": "targets_met|branches_exhausted|max_iterations",
  "test_results": [
    {
      "status": "pass",
      "method_name": "queryById",
      "test_method": "shouldReturnShopWhenIdExists",
      "branches_covered": ["id exists path"],
      "duration_ms": 45
    }
  ],
  "iterations": 3,
  "uncovered_branches": [],
  "error": null,
  "total_duration_ms": 380
}
```

## Phase 3: Evaluate & Loop

```bash
python src/main.py run
```

Or manually:
1. Run full test suite: `cd <java_project> && /home/twinkle/app/maven/bin/mvn test`
2. Generate coverage: `cd <java_project> && /home/twinkle/app/maven/bin/mvn jacoco:report`
3. Parse `target/site/jacoco/jacoco.csv` (per-class + overall)
4. Update `shared/coverage_report.json`
5. Run `state.mark_evaluation_complete()` to record checkpoint
6. If Line >= 70% and Branch >= 60% → **COMPLETE**
7. Otherwise → analyze low-coverage classes → back to Phase 2 with prioritized dispatch

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Entry point for all commands |
| `src/orchestrator.py` | Core orchestration logic |
| `src/state_manager.py` | State file read/write |
| `src/subagent_dispatch.py` | Subagent prompt building + retry tracking |
| `shared/class_list.json` | Class/method inventory |
| `shared/test_plan.json` | Iteration tracking |
| `shared/progress.txt` | Human-readable progress |
| `shared/coverage_report.json` | Coverage metrics (overall + per-class) |
| `prompts/SUBAGENT_UT_PROMPT.md` | Subagent test-writing rules (THE critical file) |
| `prompts/ORCHESTRATOR_LOOP.md` | Loop iteration prompt |
| `Rule/Java_UT_Testing_Rules.md` | UT testing standards |
| `Rule/Long_Running_Agent_Rules.md` | Long-running agent patterns |

## Container-Free Mock Strategy (CRITICAL)

ALL external dependencies MUST be mocked. NEVER depend on Docker/MySQL/Redis containers.

### MyBatis-Plus

**Chain calls CAN be mocked!** Chain calls like `query().eq().one()` internally delegate to `baseMapper` methods. Mock the `baseMapper`, not the chain:

```java
@Mock private ShopMapper baseMapper;  // baseMapper is the Mapper's internal field
@InjectMocks private ShopServiceImpl service;

// query().eq("field", val).one() → baseMapper.selectOne(wrapper)
when(baseMapper.selectOne(any(Wrapper.class))).thenReturn(entity);

// query().eq().list() → baseMapper.selectList(wrapper)
when(baseMapper.selectList(any(Wrapper.class))).thenReturn(list);

// query().orderByDesc().page() → baseMapper.selectPage(page, wrapper)
when(baseMapper.selectPage(any(Page.class), any(Wrapper.class))).thenReturn(page);

// lambdaUpdate().setSql().eq().update() → baseMapper.update(null, wrapper)
when(baseMapper.update(isNull(), any(Wrapper.class))).thenReturn(1);

// updateById(entity) → baseMapper.updateById(entity)
when(baseMapper.updateById(any(Entity.class))).thenReturn(1);
```

### Redis

```java
@Mock private StringRedisTemplate stringRedisTemplate;
@Mock private ValueOperations<String, String> valueOps;
@Mock private SetOperations<String, String> setOps;
@Mock private ZSetOperations<String, String> zSetOps;
@Mock private HashOperations<String, Object, Object> hashOps;
@Mock private ListOperations<String, String> listOps;
@Mock private GeoOperations<String, String> geoOps;
@InjectMocks private SomeServiceImpl service;

@BeforeEach
void setUp() {
    when(stringRedisTemplate.opsForValue()).thenReturn(valueOps);
    when(stringRedisTemplate.opsForSet()).thenReturn(setOps);
    when(stringRedisTemplate.opsForZSet()).thenReturn(zSetOps);
    when(stringRedisTemplate.opsForHash()).thenReturn(hashOps);
    when(stringRedisTemplate.opsForList()).thenReturn(listOps);
    when(stringRedisTemplate.opsForGeo()).thenReturn(geoOps);
}
```

### Controllers (No Spring Context)

```java
@Mock private ISomeService someService;
@InjectMocks private SomeController controller;

@Test
void shouldReturnOk() {
    when(someService.method(args)).thenReturn(Result.ok());
    Result result = controller.endpoint(args);
    assertTrue(result.getSuccess());
}
```

### Config Classes

```java
@Test
void shouldCreateBean() {
    MyConfig config = new MyConfig();
    SomeBean bean = config.someBean();
    assertNotNull(bean);
}
```

### Interceptors

Use `MockHttpServletRequest`/`MockHttpServletResponse` + `@Mock` deps.

### Common Pitfalls

- `@Data` + `@Builder` has NO no-arg constructor → use `.builder().build()`
- `hashOps.putAll()` returns void → don't stub it, use `verify` instead
- Redisson lock key: `"lock" + key` NOT `"lock:" + key`
- Add `@MockitoSettings(strictness = Strictness.LENIENT)` to avoid UnnecessaryStubbingException
- ThreadLocal cleanup: always `UserHolder.removeUser()` in `@AfterEach`

## Java Project

Tech stack: Spring Boot + MyBatis-Plus + Redis + RabbitMQ (configurable)

Maven: `/home/twinkle/app/maven/bin/mvn`
Settings: `/home/twinkle/app/maven/conf/settings.xml`

```bash
# Run specific test
cd <java_project> && /home/twinkle/app/maven/bin/mvn test -Dtest=ShopServiceImplTest#shouldReturnShopWhenIdExists

# Run all tests
cd <java_project> && /home/twinkle/app/maven/bin/mvn test

# Coverage report
cd <java_project> && /home/twinkle/app/maven/bin/mvn jacoco:report
```

## Test Naming Convention

- Class: `{ClassName}Test`
- Method: `should[Expected]When[Condition]`
- Pattern: `// Arrange` → `// Act` → `// Assert`

## Coverage Targets

| Metric | Target |
|--------|--------|
| Line coverage | >= 70% |
| Branch coverage | >= 60% |

## Completion Condition

When ALL of these are true, output `ALL_TESTS_COMPLETE`:
1. No pending methods in `class_list.json` (all have `test_status` = "pass", "fail", or classes marked "met_targets"/"exhausted")
2. `coverage_report.json` shows Line >= 70%, Branch >= 60%
3. `mvn test` passes with 0 errors

## Project-Agnostic Design

This orchestrator is designed to work with ANY Java project:
- Set `--java-project <name>` to target a different project
- All class scanning, method extraction, and mock strategies are generic
- The mock strategy adapts based on detected dependencies (MyBatis-Plus, Redis, RabbitMQ, etc.)

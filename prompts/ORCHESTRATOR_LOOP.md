# Orchestrator Loop Prompt

Use this prompt to run a single iteration of the UT generation loop
(via Ralph Loop or manual invocation).

---

Execute ONE iteration of the UT Generation Orchestrator.

## Startup

1. Read the state files in `shared/`:
   - `shared/class_list.json` - class and method inventory
   - `shared/test_plan.json` - iteration tracking
   - `shared/progress.txt` - human-readable progress
   - `shared/coverage_report.json` - coverage metrics

2. Determine the current phase based on state:
   - If class_list.json doesn't exist → **Phase 1: Init**
   - If there are pending methods (and fewer than 20 new methods since last eval) → **Phase 2: Dispatch**
   - If 20+ new methods tested since last eval → **Phase 3: Evaluate** (partial evaluation)
   - If all methods tested and coverage not met → **Phase 3: Evaluate**
   - If coverage targets met → **Complete**

## Phase 1: Initialization

Run: `python src/main.py init`

This scans `<java_project>/src/main/java/`, classifies all Java classes
(service/controller/mapper/entity/utils/config/interceptor/other),
extracts public methods, and creates `shared/class_list.json` and `shared/test_plan.json`.

### Sync Existing Tests

If the project already has test files, run:
```python
from src.state_manager import StateManager
sm = StateManager(project_root)
result = sm.sync_existing_tests("<java_project>/src/test/java/")
print(f"Synced {result['synced']} existing tests, skipped {result['skipped']}")
```

## Phase 2: Dispatch Subagents

1. Run `python src/main.py prompts` to get the current batch of subagent prompts.
2. For each prompt, use the **Agent tool** to dispatch a subagent:
   - `subagent_type`: "general-purpose"
   - `model`: "sonnet" (or "haiku" for simple getters/setters)
   - Each subagent writes ONE test method and runs `mvn test -Dtest=...`
3. Wait for all subagents to complete.
4. Collect the JSON results from each subagent into a JSON file:
   ```json
   {
     "results": [
       {
         "status": "pass",
         "class_name": "ShopServiceImpl",
         "method_name": "queryById",
         "test_method": "shouldReturnShopWhenIdExists",
         "test_file": "src/test/java/.../ShopServiceImplTest.java",
         "branches_covered": ["id exists branch"],
         "error": null,
         "duration_ms": 45
       }
     ]
   }
   ```
5. Run `python src/main.py apply --results-file results.json` to update state.

### Dispatch Strategy

- Max 5 subagents per batch (3 for complex methods)
- Never dispatch two subagents for the **same class** in one batch (file conflict)
- Use background mode for parallel execution
- **Prioritize complex methods first** (they need multiple tests for branch coverage)
- **Prioritize low-coverage classes** over high-coverage ones

### Retry Strategy for Failed Subagents

- Max 3 retries per method
- On retry, provide the previous error message to the subagent
- Common failures to diagnose:
  - Missing `@MockitoSettings(strictness = Strictness.LENIENT)` → add to class
  - Wrong MyBatis-Plus update() args → use `update(isNull(), any(Wrapper.class))`
  - Wrong Redis key pattern → check the actual key concatenation
  - `hashOps.putAll()` returns void → don't stub, use `verify` instead
  - Lombok @Builder + @Data → use `.builder()` not `new`
- If a method fails 3 times, mark it as `fail` and move on (document the reason)

## Phase 3: Evaluation

1. Run all tests: `cd <java_project> && /home/twinkle/app/maven/bin/mvn test`
2. Generate coverage: `cd <java_project> && /home/twinkle/app/maven/bin/mvn jacoco:report`
3. Parse coverage from `<java_project>/target/site/jacoco/jacoco.csv`
4. Update `shared/coverage_report.json` with current coverage metrics
5. Run `state.mark_evaluation_complete()` to record evaluation checkpoint

### Coverage Analysis

After evaluation:
- Check per-class coverage in `coverage_report.json` → `per_class` array
- Identify classes below 50% line coverage → these need more tests
- Identify methods in those low-coverage classes that are still pending
- Prioritize those methods in the next Phase 2 dispatch

### Coverage Targets

If Line >= 70% and Branch >= 60%:
- Output: `ALL_TESTS_COMPLETE`
- Stop the loop

If coverage targets NOT met:
- Check the coverage gap: how far from 70% line / 60% branch?
- For large gaps (>20%): dispatch more complex-method tests
- For small gaps (<10%): focus on specific low-coverage classes
- Reset any stale `in_progress` methods back to `pending`
- Continue with Phase 2

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Subagent writes test that doesn't compile | Check imports, correct mock types, run `mvn test` to get exact error |
| Test passes locally but fails in full suite | Check for ThreadLocal contamination (add @AfterEach cleanup) |
| Coverage not improving | Subagents may test already-covered paths; focus on uncovered branches |
| MyBatis-Plus chain mock fails | Mock baseMapper methods, not chain. Chain calls delegate to baseMapper. |
| Redis mock NPE | Wire up all ops types in @BeforeEach; mock each ops type separately |
| UserHolder not set | Call `UserHolder.saveUser(user)` in @BeforeEach, remove in @AfterEach |

## Completion

When done with this iteration, output a summary:
- What was accomplished (tests written, passed, failed)
- Current coverage metrics (line %, branch %, method %)
- Coverage gap remaining
- Per-class coverage for bottom 5 classes
- Next action (dispatch / evaluate / complete)

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
   - If there are pending methods → **Phase 2: Dispatch**
   - If all methods tested and coverage not met → **Phase 3: Evaluate**
   - If coverage targets met → **Complete**

## Phase 1: Initialization

Run: `python src/main.py init`

This scans `dianping/src/main/java/`, classifies all Java classes,
extracts public methods, and creates `shared/class_list.json` and `shared/test_plan.json`.

## Phase 2: Dispatch Subagents

1. Run `python src/main.py prompts` to get the current batch of subagent prompts.
2. For each prompt, use the **Agent tool** to dispatch a subagent:
   - `subagent_type`: "general-purpose"
   - `model`: "sonnet"
   - Each subagent writes ONE test method and runs `mvn test -Dtest=...`
3. Wait for all subagents to complete.
4. Collect the JSON results from each subagent into a file.
5. Run `python src/main.py apply --results-file results.json` to update state.

Dispatch strategy:
- Max 5 subagents per batch
- Never dispatch two subagents for the same class in one batch
- Use background mode for parallel execution

## Phase 3: Evaluation

1. Run: `cd dianping && /home/twinkle/app/maven/bin/mvn test`
2. Run: `cd dianping && /home/twinkle/app/maven/bin/mvn jacoco:report`
3. Parse coverage from `dianping/target/site/jacoco/jacoco.csv`
4. Update `shared/coverage_report.json` with current coverage metrics

If coverage targets (Line >= 70%, Branch >= 60%) are met:
- Output: `ALL_TESTS_COMPLETE`
- Stop the loop

If coverage targets NOT met:
- Continue with Phase 2 to generate more tests
- Focus on classes with low coverage

## Completion

When done with this iteration, output a summary:
- What was accomplished
- Current coverage metrics
- Next action needed

# Plan: Orchestrator-Subagent Architecture for Java UT Auto-Generation

## Context

### Problem Statement

Traditional Java UT generation depends on containers (Redis/MySQL/Kafka) or Spring Boot Test context, limiting where tests can run. This plan designs a **container-free** multi-agent system that mocks ALL external dependencies with Mockito, making UT tests runnable anywhere (CI/local, no Docker required).

### Solution

**Orchestrator + Subagent architecture**, fully based on Claude Code's built-in Agent tool:

- **Orchestrator**: Long-running coordinator agent that scans projects, plans tests, dispatches subagents, collects results, and evaluates coverage
- **Subagent**: One-shot agent that writes ONE test method, runs `mvn test -Dtest=...` to verify, and returns results

**Core characteristics**:
- One Subagent = One test method (method-level granularity)
- Subagent writes code + runs test verification itself
- Orchestrator dispatches subagents in parallel (different classes = no file conflicts)
- **Zero container dependencies**: All external deps (DB/Cache/MQ/HTTP) mocked via Mockito
- Fully based on Claude Code built-in mechanisms
- **Adaptable to any Java project** (Spring Boot / MyBatis-Plus / JPA / Redis / Kafka / etc.)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Orchestrator (Long-Running)                      │
│                                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                 │
│  │ Phase 1      │   │ Phase 2      │   │ Phase 3      │                 │
│  │ Scan & Plan  │──▶│ Dispatch     │──▶│ Evaluate     │──┐              │
│  │              │   │ Subagents    │   │ & Loop       │  │              │
│  └──────────────┘   └──────────────┘   └──────────────┘  │              │
│         │                  │                  │           │              │
│         ▼                  ▼                  ▼           │              │
│  ┌──────────────┐   ┌──────────────────┐   ┌──────────┐  │              │
│  │Scan src/main │   │ Agent tool parallel│  │ mvn test │  │              │
│  │Classify +    │   │Dispatch N Subagents│  │ jacoco   │  │              │
│  │extract methods│  │Each writes 1 test  │  │ Check cov│──┘              │
│  │→ class_list │   │Each self-tests     │   │ Not met? │  continue loop │
│  │→ test_plan  │   │Returns result      │   └──────────┘                 │
│  └──────────────┘   └──────────────────┘                                 │
│                                                                          │
│                       State Files (shared/)                               │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ class_list.json │ test_plan.json │ progress.txt │ coverage_report │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

Subagent (One-Shot):
  ┌──────────────────────────────────────────────┐
  │  Input: className + methodName + signature   │
  │         + source code path + type + complexity│
  │                                              │
  │  1. Read target method source code            │
  │  2. Analyze logic, design test case (AAA)     │
  │  3. Write JUnit 5 test method (Mock all deps) │
  │  4. Run mvn test -Dtest=Class#method verify   │
  │  5. Return: {pass/fail, branches, error, time}│
  └──────────────────────────────────────────────┘
```

---

## Container-Free Mock Strategy

### Core Principle

**Never depend on containers or external environments.** All tests are pure unit tests — no Redis/MySQL/Docker/Kafka required.

### Universal Mock Patterns

#### ORM Layer Mock

| Framework | Dependency Type | Mock Approach |
|-----------|----------------|---------------|
| MyBatis-Plus ServiceImpl | `baseMapper` field | `@Mock Mapper` + `@InjectMocks ServiceImpl`, mock `baseMapper.selectOne/selectList/selectPage/update/updateById/insert/delete` |
| MyBatis Mapper | `@Autowired Mapper` | `@Mock Mapper`, mock custom SQL methods |
| Spring Data JPA | `JpaRepository` | `@Mock Repository`, mock `findById/save/findAll` |
| Hibernate | `SessionFactory` | `@Mock SessionFactory` + `@Mock Session` |
| JDBC Template | `JdbcTemplate` | `@Mock JdbcTemplate`, mock `query/update` |

**MyBatis-Plus chain call mock principle**:
```
query().eq("field", val).one()
  → LambdaQueryChainWrapper(baseMapper)
  → .eq(...) returns this
  → .one() calls baseMapper.selectOne(wrapper)
  → Mock baseMapper.selectOne(any()) intercepts it

Chain → baseMapper mapping:
  query().eq().one()              → baseMapper.selectOne(any(Wrapper.class))
  query().eq().list()             → baseMapper.selectList(any(Wrapper.class))
  query().orderByDesc().page()    → baseMapper.selectPage(any(Page.class), any(Wrapper.class))
  lambdaQuery().eq().one()        → baseMapper.selectOne(any(Wrapper.class))
  lambdaUpdate().setSql().eq().update() → baseMapper.update(null, any(Wrapper.class))
  update().setSql().eq().update() → baseMapper.update(null, any(Wrapper.class))
  lambdaUpdate().set().eq().update()    → baseMapper.update(entity, any(Wrapper.class))
```

#### Cache Layer Mock

| Framework | Mock Approach |
|-----------|--------------|
| Spring Redis `StringRedisTemplate` | `@Mock StringRedisTemplate` + mock each ops: `ValueOperations`, `SetOperations`, `ZSetOperations`, `HashOperations`, `ListOperations`, `GeoOperations` |
| Spring Redis `RedisTemplate<K,V>` | Same pattern, mock ops types used by the code |
| Caffeine `Cache` | `@Mock Cache<K,V>`, mock `get/put/invalidate` |
| Ehcache | `@Mock CacheManager` + `@Mock Cache` |

#### MQ Layer Mock

| Framework | Mock Approach |
|-----------|--------------|
| RabbitMQ `RabbitTemplate` | `@Mock RabbitTemplate`, mock `convertAndSend/receiveAndConvert` |
| Kafka `KafkaTemplate` | `@Mock KafkaTemplate`, mock `send` |
| RocketMQ `RocketMQTemplate` | `@Mock RocketMQTemplate`, mock `syncSend` |

#### HTTP Client Mock

| Framework | Mock Approach |
|-----------|--------------|
| `RestTemplate` | `@Mock RestTemplate`, mock `getForObject/postForEntity` |
| `WebClient` | `@Mock WebClient` + mock chain |
| OpenFeign `@FeignClient` | `@MockBean FeignClient` or mock service layer |
| OkHttp `OkHttpClient` | `@Mock OkHttpClient` |

#### Other Common Dependency Mocks

| Dependency | Mock Approach |
|-----------|--------------|
| ThreadLocal utils (e.g., UserHolder) | `@BeforeEach` set value, `@AfterEach` remove |
| `HttpSession` / `HttpServletRequest` | `MockHttpServletRequest` / `MockHttpServletResponse` from spring-test |
| Redisson `RedissonClient` + `RLock` | `@Mock RedissonClient` + `@Mock RLock`, mock `getLock/tryLock` |
| `MultipartFile` | `mock(MultipartFile.class)` |
| `Clock` / `LocalDateTime.now()` | Use fixed values (time is predictable) |
| Filesystem operations | Mock or use `@TempDir` (JUnit 5) |

### Controller Test Pattern

**Do NOT use `@WebMvcTest`** (loads Spring context, triggers Redis/DB bean initialization failures).

Use `@InjectMocks` with `@Mock` services instead:

```java
@ExtendWith(MockitoExtension.class)
class XxxControllerTest {
    @Mock private XxxService xxxService;
    @Mock private YyyService yyyService;
    @InjectMocks private XxxController controller;

    @Test
    void shouldReturnOkWhenCondition() {
        when(xxxService.method(args)).thenReturn(Result.ok());
        Result result = controller.endpoint(args);
        assertTrue(result.getSuccess());
    }
}
```

### Config Class Test Pattern

```java
@Test
void shouldCreateBean() {
    MyConfig config = new MyConfig();
    SomeBean bean = config.someBean();
    assertNotNull(bean);
    assertEquals("expected", bean.getProperty());
}
```

### Interceptor Test Pattern

```java
@Mock private StringRedisTemplate stringRedisTemplate;
@Mock private HashOperations<String, Object, Object> hashOps;
private RefreshTokenInterceptor interceptor;
private MockHttpServletRequest request;
private MockHttpServletResponse response;

@BeforeEach
void setUp() {
    interceptor = new RefreshTokenInterceptor(stringRedisTemplate);
    request = new MockHttpServletRequest();
    response = new MockHttpServletResponse();
    when(stringRedisTemplate.opsForHash()).thenReturn(hashOps);
}

@AfterEach
void tearDown() {
    UserHolder.removeUser();
}

@Test
void shouldAllowWhenNoToken() throws Exception {
    assertTrue(interceptor.preHandle(request, response, null));
}
```

---

## Three-Phase Lifecycle

### Phase 1: Scan & Plan

1. Scan all `.java` files under `{PROJECT}/src/main/java/`
2. Classify by type: `service/controller/mapper/entity/utils/config/interceptor/other`
3. For each class, extract all public methods (signature, params, return type)
4. Skip trivial getters/setters and constructors
5. Generate `shared/class_list.json` (method-level granularity)
6. Generate `shared/test_plan.json`
7. Generate `shared/progress.txt`
8. Optionally: sync existing test files to mark already-tested methods

**class_list.json structure**:
```json
{
  "project_path": "{PROJECT_PATH}",
  "scan_date": "YYYY-MM-DD",
  "classes": [
    {
      "name": "ClassName",
      "package": "com.example.package",
      "path": "src/main/java/...",
      "type": "service|controller|mapper|entity|utils|config|interceptor|other",
      "priority": 1,
      "test_file": "src/test/java/.../ClassNameTest.java",
      "methods": [
        {
          "name": "methodName",
          "signature": "public ReturnType methodName(ParamType param)",
          "test_status": "pending|in_progress|pass|fail",
          "test_method": "shouldExpectedWhenCondition",
          "complexity": "simple|medium|complex"
        }
      ]
    }
  ]
}
```

### Phase 2: Dispatch Subagents

1. Get `test_status=pending` methods from `class_list.json`
2. Sort by priority + complexity (complex first — needs more branch coverage)
3. Select 3-5 methods from different classes (avoid file conflicts)
4. Dispatch subagents via Claude Code Agent tool in parallel
5. Each subagent receives:
   - Exact method to test (class, method, signature, source path)
   - Type-specific mock strategy guidance
   - Branch coverage instructions
   - Retry count (if re-attempting)
6. Collect subagent JSON results, update state files

### Phase 3: Evaluate & Loop

1. Run `mvn test` (full suite)
2. Run `mvn jacoco:report`
3. Parse coverage report → `coverage_report.json` (overall + per-class)
4. Line >= 70% AND Branch >= 60% → **COMPLETE**
5. Not met → analyze low-coverage classes → back to Phase 2 with prioritized dispatch

**Partial evaluation**: Trigger evaluation every ~20 new methods (not just when ALL methods are done) to enable course correction mid-run.

---

## State Files (shared/)

| File | Purpose |
|------|---------|
| `class_list.json` | Full class + method inventory with test status |
| `test_plan.json` | Iteration tracking, batch config, failed methods |
| `progress.txt` | Human-readable progress log |
| `coverage_report.json` | Overall + per-class coverage metrics |

All state file fields are generic — no project-specific references.

---

## Project Structure

```
{PROJECT_ROOT}/
├── CLAUDE.md                          # Orchestrator instructions (project entry)
├── Plan/
│   └── orchestrator-architecture.md   # This architecture document
├── Rule/
│   ├── Java_UT_Testing_Rules.md       # Java UT testing standards
│   ├── Long_Running_Agent_Rules.md    # Long-running agent patterns
│   └── subagent-guide.md             # Claude Code Subagent usage guide
├── src/                               # Python orchestration code
│   ├── main.py                        # Entry point (init/status/run/loop/prompts/apply/reset)
│   ├── orchestrator.py                # Three-phase orchestration logic
│   ├── state_manager.py               # shared/ state file management
│   └── subagent_dispatch.py           # Subagent prompt builder + retry tracking
├── prompts/
│   ├── SUBAGENT_UT_PROMPT.md          # Subagent UT writing rules (incl. mock strategy)
│   └── ORCHESTRATOR_LOOP.md           # Loop iteration prompt template
├── shared/                            # Runtime state files
│   ├── class_list.json
│   ├── test_plan.json
│   ├── progress.txt
│   └── coverage_report.json
└── {JAVA_PROJECT}/                    # Target Java project (user-specified)
    ├── pom.xml (or build.gradle)
    └── src/main/java/
```

---

## Subagent Dispatch Protocol

### Prompt Template (Auto-Filled)

The subagent prompt is built by `subagent_dispatch.py` and includes:
- Exact target (class, method, signature, source/test paths)
- Type-specific mock strategy based on class type (service/controller/interceptor/config/utils)
- Branch coverage guidance based on method complexity (simple/medium/complex)
- Retry context if re-attempting a failed method

See `prompts/SUBAGENT_UT_PROMPT.md` for the full subagent instructions.

### Subagent Return Format

```json
{
  "status": "pass|fail",
  "class_name": "ClassName",
  "method_name": "methodName",
  "test_method": "testMethodName",
  "test_file": "src/test/java/.../ClassNameTest.java",
  "branches_covered": ["branch description 1", "branch description 2"],
  "error": "error message if failed, null if passed",
  "duration_ms": 45
}
```

---

## Orchestrator Startup

```bash
cd {PROJECT_ROOT}
python src/main.py init [--java-project {JAVA_PROJECT}] [--force]
python src/main.py status
python src/main.py loop --max-iterations 200

# Individual commands:
python src/main.py prompts                   # Get current batch prompts
python src/main.py apply -f results.json     # Apply subagent results
python src/main.py reset --force             # Reset all state
```

---

## Verification Checklist

```
□ All tests pass (mvn test, 0 failures)
□ Coverage targets met (Line ≥ 70%, Branch ≥ 60%)
□ No Redis/MySQL/Docker required to run
□ All methods in class_list.json have test_status = pass
□ Config, Interceptor, Utility classes all have tests
□ Adaptable to any Java project
□ Per-class coverage tracked in coverage_report.json
```

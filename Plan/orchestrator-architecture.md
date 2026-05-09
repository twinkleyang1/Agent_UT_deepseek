# Plan: Orchestrator-Subagent Architecture for Java UT Auto-Generation

## Context

### Problem Statement

传统的 Java UT 生成依赖容器（Redis/MySQL/Kafka）或 Spring Boot Test 上下文，导致测试受限于环境。本方案设计一个**纯容器无关**的多 Agent 系统，通过全面 Mock 外部依赖，让 UT 测试在任何环境（CI/本地）都能运行。

### Solution

**Orchestrator + Subagents 架构**，完全基于 Claude Code 内置 Agent 工具：

- **Orchestrator**：长期运行的编排者 Agent，扫描项目、规划测试、派发 subagent、收集结果、评估覆盖率
- **Subagent**：一次性 Agent，每次只为一个方法编写一个测试函数，写完立即运行 `mvn test -Dtest=...` 验证，返回结果

**核心特点**：
- 一个 Subagent = 一个测试方法（函数级粒度）
- Subagent 自己写代码 + 运行测试验证
- Orchestrator 并行派发 Subagent（不同类的方法互不冲突）
- **零容器依赖**：全部外部依赖（DB/Cache/MQ/HTTP）通过 Mockito 模拟
- 完全基于 Claude Code 内置机制
- **适配任意 Java 项目**（Spring Boot / MyBatis-Plus / JPA / Redis / Kafka 等）

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Orchestrator (长期运行)                          │
│                                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                 │
│  │ Phase 1      │   │ Phase 2      │   │ Phase 3      │                 │
│  │ Scan & Plan  │──▶│ Dispatch     │──▶│ Evaluate     │──┐              │
│  │              │   │ Subagents    │   │ & Loop       │  │              │
│  └──────────────┘   └──────────────┘   └──────────────┘  │              │
│         │                  │                  │           │              │
│         ▼                  ▼                  ▼           │              │
│  ┌──────────────┐   ┌──────────────────┐   ┌──────────┐  │              │
│  │扫描 src/main │   │ Agent tool 并行   │   │ mvn test │  │              │
│  │分类 + 方法列表│   │派发 N 个 Subagent │   │ jacoco   │  │              │
│  │→ class_list │   │每个写1个测试方法   │   │ 检查覆盖率│──┘              │
│  │→ test_plan  │   │每个自测返回结果    │   │ 未达标?   │  继续循环       │
│  └──────────────┘   └──────────────────┘   └──────────┘                 │
│                                                                          │
│                          State Files (shared/)                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ class_list.json │ test_plan.json │ progress.txt │ coverage_report │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

Subagent (一次性):
  ┌──────────────────────────────────────────────┐
  │  输入: 类名 + 方法名 + 方法签名 + 源代码      │
  │                                              │
  │  1. 读取目标方法的源代码                      │
  │  2. 分析逻辑，设计测试用例 (AAA)              │
  │  3. 编写 JUnit 5 测试方法（Mock 所有外部依赖）│
  │  4. 运行 mvn test -Dtest=Class#method 验证    │
  │  5. 返回结果: {pass/fail, error_msg, time}    │
  └──────────────────────────────────────────────┘
```

---

## Container-Free Mock Strategy (容器无关 Mock 策略)

### 核心原则

**绝不依赖容器或外部环境**。所有测试必须是纯单元测试，无需启动 Redis/MySQL/Docker/Kafka。

### 通用 Mock 模式

#### ORM 层 Mock

| 框架 | 依赖类型 | Mock 方式 |
|------|---------|----------|
| MyBatis-Plus ServiceImpl | `baseMapper` 字段 | `@Mock Mapper` + `@InjectMocks ServiceImpl`，Mock `baseMapper.selectOne/selectList/insert/update/delete` |
| MyBatis Mapper | `@Autowired Mapper` | `@Mock Mapper`，Mock 自定义 SQL 方法 |
| Spring Data JPA | `JpaRepository` | `@Mock Repository`，Mock `findById/save/findAll` |
| Hibernate | `SessionFactory` | `@Mock SessionFactory` + `@Mock Session` |
| JDBC Template | `JdbcTemplate` | `@Mock JdbcTemplate`，Mock `query/update` |

**MyBatis-Plus 链式调用 Mock 原理**：
```
query().eq("field", val).one()
  → LambdaQueryChainWrapper(baseMapper)
  → .eq(...) 返回 this
  → .one() 调用 baseMapper.selectOne(wrapper)
  → Mock baseMapper.selectOne(any()) 即可拦截
```

#### Cache 层 Mock

| 框架 | Mock 方式 |
|------|----------|
| Spring Redis `StringRedisTemplate` | `@Mock StringRedisTemplate` + `mock(ValueOperations.class)` / `mock(ListOperations.class)` / `mock(HashOperations.class)` / `mock(ZSetOperations.class)` / `mock(SetOperations.class)` |
| Spring Redis `RedisTemplate<K,V>` | 同上，根据实际使用的 ops 类型 mock |
| Caffeine `Cache` | `@Mock Cache<K,V>`，Mock `get/put/invalidate` |
| Ehcache | `@Mock CacheManager` + `@Mock Cache` |

#### MQ 层 Mock

| 框架 | Mock 方式 |
|------|----------|
| RabbitMQ `RabbitTemplate` | `@Mock RabbitTemplate`，Mock `convertAndSend/receiveAndConvert` |
| Kafka `KafkaTemplate` | `@Mock KafkaTemplate`，Mock `send` |
| RocketMQ `RocketMQTemplate` | `@Mock RocketMQTemplate`，Mock `syncSend` |

#### HTTP 客户端 Mock

| 框架 | Mock 方式 |
|------|----------|
| `RestTemplate` | `@Mock RestTemplate`，Mock `getForObject/postForEntity` |
| `WebClient` | `@Mock WebClient` + mock chain |
| OpenFeign `@FeignClient` | `@MockBean FeignClient` 或 Mock Service 层 |
| OkHttp `OkHttpClient` | `@Mock OkHttpClient` |

#### 其他常见依赖 Mock

| 依赖 | Mock 方式 |
|------|----------|
| ThreadLocal 工具类 (如 UserHolder) | `@BeforeEach` 中 `set(value)`，`@AfterEach` 中 `remove()` |
| `HttpSession` / `HttpServletRequest` | `mock(HttpSession.class)` / `mock(HttpServletRequest.class)` |
| `MultipartFile` | `mock(MultipartFile.class)` |
| `Clock` / `LocalDateTime.now()` | 使用固定值，不 mock（时间结果是可预测的） |
| 文件系统操作 | Mock 或使用 `@TempDir` (JUnit 5) |

### Controller 测试模式

**不使用 `@WebMvcTest`**（会加载 Spring 上下文，触发 Redis/DB bean 初始化失败）。

改用 `ReflectionTestUtils.setField()` 注入 Mock：

```java
@ExtendWith(MockitoExtension.class)
class XxxControllerTest {

    @Mock private XxxService xxxService;  // Controller 依赖的 Service
    @Mock private YyyService yyyService;  // Controller 依赖的另一个 Service

    private XxxController controller;

    @BeforeEach
    void setUp() {
        controller = new XxxController();
        ReflectionTestUtils.setField(controller, "xxxService", xxxService);
        ReflectionTestUtils.setField(controller, "yyyService", yyyService);
    }

    @Test
    void shouldReturnExpectedWhenCondition() {
        when(xxxService.method()).thenReturn(expectedResult);
        Result result = controller.endpoint();
        assertNotNull(result);
    }
}
```

---

## Three-Phase Lifecycle

### Phase 1: Scan & Plan (扫描与规划)

1. 扫描 `{PROJECT}/src/main/java/` 下所有 `.java` 文件
2. 按类型分类：`service/controller/repository/entity/utils/config/other`
3. 对每个类，提取所有 public 方法（方法签名、参数、返回类型）
4. 生成 `shared/class_list.json`（方法级粒度）
5. 生成 `shared/test_plan.json`
6. 生成 `shared/progress.txt`

**class_list.json 结构**：
```json
{
  "project_path": "{PROJECT_PATH}",
  "scan_date": "YYYY-MM-DD",
  "classes": [
    {
      "name": "ClassName",
      "package": "com.example.package",
      "path": "src/main/java/...",
      "type": "service|controller|mapper|entity|utils|config|other",
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

### Phase 2: Dispatch Subagents (派发子代理)

1. 从 `class_list.json` 获取 `test_status=pending` 的方法
2. 按优先级排序，选择不同类的 3-5 个方法（避免文件冲突）
3. 通过 Claude Code Agent 工具并行派发 Subagent
4. 每个 Subagent 接收精确的任务描述，内含 Mock 策略指导
5. 收集 Subagent JSON 结果，更新状态文件

### Phase 3: Evaluate & Loop (评估与循环)

1. 运行 `mvn test` (全量)
2. 运行 `mvn jacoco:report`
3. 解析覆盖率报告 → `coverage_report.json`
4. Line >= 70% 且 Branch >= 60% → 完成
5. 未达标 → 分析未覆盖方法 → 回到 Phase 2

---

## State Files (shared/)

`class_list.json` | `test_plan.json` | `progress.txt` | `coverage_report.json`

状态文件不包含任何具体项目细节，字段名称通用化。

---

## Project Structure

```
{PROJECT_ROOT}/
├── CLAUDE.md                          # Orchestrator 指令 (项目入口)
├── Plan/
│   └── orchestrator-architecture.md   # 本架构设计文档
├── Rule/
│   ├── Java_UT_Testing_Rules.md       # Java UT 编写规范
│   ├── Long_Running_Agent_Rules.md    # 长时间运行 Agent 规范
│   └── subagent-guide.md             # Claude Code Subagent 使用指南
├── src/                               # Python 编排代码
│   ├── main.py                        # 入口 (init/status/run/loop/prompts/apply/reset)
│   ├── orchestrator.py                # 三阶段编排逻辑
│   ├── state_manager.py               # shared/ 状态文件管理
│   └── subagent_dispatch.py           # Subagent prompt 生成 + 结果解析
├── prompts/
│   ├── SUBAGENT_UT_PROMPT.md          # Subagent UT 编写规范 (含 Mock 策略)
│   └── ORCHESTRATOR_LOOP.md           # 循环迭代 prompt 模板
├── shared/                            # 运行时状态文件
│   ├── class_list.json
│   ├── test_plan.json
│   ├── progress.txt
│   └── coverage_report.json
└── {JAVA_PROJECT}/                    # 目标 Java 项目 (用户指定)
    ├── pom.xml (或 build.gradle)
    └── src/main/java/
```

---

## Dispatch Protocol

### Subagent Prompt 模板（通用）

根据目标方法自动填充 Mock 策略建议：

```
你是 Java UT 编写专家。

目标类: {package}.{ClassName}
目标方法: {methodName}({params}) → {returnType}

任务:
1. 阅读源码理解方法逻辑
2. 分析该方法依赖了哪些外部组件：
   - ORM 操作？→ Mock baseMapper / Repository
   - Redis 操作？→ Mock StringRedisTemplate / RedisTemplate
   - MQ 操作？→ Mock RabbitTemplate / KafkaTemplate
   - HTTP 调用？→ Mock RestTemplate / WebClient
   - 其他 Service？→ Mock 被调用的 Service
   - ThreadLocal？→ @BeforeEach 中 set, @AfterEach 中 remove
3. 设计 AAA 测试用例
4. 编写 JUnit 5 + Mockito 测试方法
5. 运行 mvn test -Dtest=ClassNameTest#testMethodName
6. 返回 JSON: {"status": "pass|fail", ...}
```

### Subagent 返回格式

```json
{
  "status": "pass|fail",
  "class_name": "ClassName",
  "method_name": "methodName",
  "test_method": "testMethodName",
  "test_file": "src/test/java/.../ClassNameTest.java",
  "error": null,
  "duration_ms": 45
}
```

---

## Orchestrator 启动

```bash
cd {PROJECT_ROOT} && python src/main.py init --java-project {JAVA_PROJECT}
python src/main.py status
python src/main.py loop --max-iterations 200
```

---

## Verification

```
□ 所有测试通过 (mvn test, 0 failures)
□ 覆盖率达标 (Line ≥ 70%, Branch ≥ 60%)
□ 无需 Redis/MySQL/Docker 即可运行
□ class_list.json 所有方法 test_status = pass
□ 适配任意 Java 项目
```

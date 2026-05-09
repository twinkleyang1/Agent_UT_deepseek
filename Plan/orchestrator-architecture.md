# Plan: Orchestrator-Subagent Architecture for Java UT Auto-Generation

## Context

### Problem Statement

现有 `Agent_UT` 项目采用 Planner → Generator → Evaluator 三角色线性架构，依赖 Python Harness (`MutiagentUT/main.py`) 协调状态，通过状态文件驱动循环。该架构存在以下问题：

1. **串行瓶颈**：Generator 一次只处理一个类，无法并行生成测试
2. **粒度粗糙**：以类为单位，评估反馈太慢，上下文容易膨胀
3. **外部依赖**：依赖 Python Harness 和 Ralph Loop 插件实现循环

### Solution

设计全新的 **Orchestrator + Subagents 架构**，完全基于 Claude Code 内置的 Agent 工具：

- **Orchestrator**：长期运行的编排者 Agent，负责扫描项目、规划测试、派发 subagent、收集结果、评估覆盖率
- **Subagent**：一次性 Agent，每次只为一个 Java 方法编写一个 UT 测试函数，写完立即运行 `mvn test -Dtest=...` 验证，返回结果给 Orchestrator

**核心特点**：
- 一个 Subagent = 一个测试方法 (函数级粒度)
- Subagent 自己写代码 + 自己运行测试验证
- Orchestrator 可并行派发多个 Subagent（不同类的方法互不冲突）
- 完全基于 Claude Code 内置机制，零外部依赖

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
│  │扫描 src/main/│   │ Agent tool 并行   │   │ mvn test │  │              │
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

Subagent (一次性，用完即弃):
  ┌──────────────────────────────────────────────┐
  │  输入: 类名 + 方法名 + 方法签名 + 源代码      │
  │                                              │
  │  1. 读取目标方法的源代码                      │
  │  2. 分析逻辑，设计测试用例 (AAA)              │
  │  3. 编写 JUnit 5 测试方法                     │
  │  4. 运行 mvn test -Dtest=Class#method 验证    │
  │  5. 返回结果: {pass/fail, error_msg, time}    │
  └──────────────────────────────────────────────┘
```

---

## Three-Phase Lifecycle

### Phase 1: Scan & Plan (扫描与规划)

**Orchestrator 执行**：

1. 扫描 `dianping/src/main/java/` 下所有 `.java` 文件
2. 按类型分类：service/controller/mapper/entity/utils/other
3. 对每个类，提取所有 public 方法（包括方法签名、参数、返回类型）
4. 生成 `shared/class_list.json` - 带方法级别的粒度
5. 生成 `shared/test_plan.json` - 每个方法一条待生成的测试记录
6. 生成 `shared/progress.txt` - 初始进度文件

**class_list.json 结构 (方法级)**：
```json
{
  "project_path": "/home/twinkle/app/808/Agent_UT_deepseek/dianping",
  "scan_date": "2026-05-09",
  "classes": [
    {
      "name": "ShopServiceImpl",
      "package": "com.hmdp.service.impl",
      "path": "src/main/java/com/hmdp/service/impl/ShopServiceImpl.java",
      "type": "service",
      "priority": 1,
      "test_file": "src/test/java/com/hmdp/service/impl/ShopServiceImplTest.java",
      "methods": [
        {
          "name": "queryById",
          "signature": "public Result queryById(Long id)",
          "test_status": "pending",
          "test_method": "shouldReturnShopWhenIdExists",
          "complexity": "medium"
        }
      ]
    }
  ]
}
```

### Phase 2: Dispatch Subagents (派发子代理)

**Orchestrator 执行**：

1. 从 `class_list.json` 获取所有 `test_status=pending` 的方法
2. 按优先级排序，选择不冲突的类（不同类的测试可以并行写）
3. 通过 Claude Code 的 `Agent` 工具并行派发 Subagent（建议并发数 3-5 个）
4. 每个 Subagent 接收精确的任务描述：

```
Subagent Prompt:
  你是一个 Java UT 编写专家。
  
  目标类: com.hmdp.service.impl.ShopServiceImpl
  目标方法: queryById(Long id) → Result
  方法签名: public Result queryById(Long id)
  测试类路径: src/test/java/com/hmdp/service/impl/ShopServiceImplTest.java
  测试方法名: shouldReturnShopWhenIdExists
  
  任务:
  1. 阅读 src/main/java/com/hmdp/service/impl/ShopServiceImpl.java 的 queryById 方法
  2. 设计测试用例 (AAA: Arrange-Act-Assert)
  3. 将测试方法追加到测试类文件中 (如果测试类不存在则创建)
  4. 运行: cd dianping && /home/twinkle/app/maven/bin/mvn test -Dtest=ShopServiceImplTest#shouldReturnShopWhenIdExists
  5. 返回 JSON: {"status": "pass|fail", "test_method": "shouldReturnShopWhenIdExists", "error": "", "duration_ms": 123}
  
  Mock 规则: 所有外部依赖 (Redis/MyBatis/DB) 用 @Mock
  命名规范: should[Expected]When[Condition]
```

5. Orchestrator 收集 Subagent 返回的结果
6. 更新 `class_list.json` → 标记方法的 `test_status` 为 `pass` 或 `fail`
7. 更新 `progress.txt`

**并行策略**：
- 同一时间只调度不同类的 Subagent（避免文件冲突）
- 每个批次 3-5 个 Subagent 并行
- 失败的 Subagent 记录错误信息，由 Orchestrator 决定重试或标记

### Phase 3: Evaluate & Loop (评估与循环)

**Orchestrator 执行**：

1. 运行全量测试：`mvn test`（确保所有测试互相兼容）
2. 运行覆盖率报告：`mvn jacoco:report`
3. 解析 JaCoCo 报告，更新 `shared/coverage_report.json`
4. 判断覆盖率是否达标：
   - Line >= 70% 且 Branch >= 60% → **完成**
   - 未达标 → 分析未覆盖的方法，回到 Phase 2 继续生成
5. 如果所有方法都已测试但覆盖率仍未达标 → 需要更多/更好的测试用例 → 回到 Phase 1 重新规划

---

## State Files (shared/)

### class_list.json
全量类和方法清单，跟踪每个方法的测试状态。

| 字段 | 类型 | 说明 |
|------|------|------|
| classes[].name | string | 类名 |
| classes[].methods[].test_status | enum | `pending` / `in_progress` / `pass` / `fail` |
| classes[].methods[].test_method | string | 对应的测试方法名 |

### test_plan.json
测试计划，记录每轮迭代的测试生成策略。

```json
{
  "plan_version": "1.0",
  "iteration": 3,
  "coverage_target": { "line": 0.70, "branch": 0.60 },
  "batch_size": 5,
  "current_batch": ["ShopServiceImpl", "UserController", "RegexUtils"],
  "completed_methods": 45,
  "total_methods": 200,
  "failed_methods": [
    { "class": "VoucherOrderServiceImpl", "method": "seckillVoucher", "reason": "Redis mock 超时" }
  ]
}
```

### progress.txt
人类可读的进度日志。

```
# UT Generation Progress
Last Updated: 2026-05-09 15:30:00
Iteration: 3

## Stats
- Methods tested: 45/200 (22.5%)
- Coverage: Line 35%, Branch 18%

## Last Batch (Iteration 3)
- ✓ ShopServiceImpl.queryById (pass, 45ms)
- ✓ UserController.getUser (pass, 38ms)
- ✗ VoucherOrderServiceImpl.seckillVoucher (fail: Redis connection)

## Pending Priority (Next Batch)
- BlogServiceImpl.queryHotBlog
- ShopTypeController.list
```

### coverage_report.json
覆盖率追踪（由 Phase 3 更新）。

---

## Agent Definitions

### Orchestrator (CLAUDE.md)

文件位置: `/home/twinkle/app/808/Agent_UT_deepseek/CLAUDE.md`

指导 Claude Code 作为 Orchestrator 运行。核心职责：
1. 读取 shared/ 了解当前状态
2. 判断当前所属 phase
3. Phase 1 → 扫描项目，创建状态文件
4. Phase 2 → 并行派发 Subagent（使用 Agent 工具）
5. Phase 3 → 运行全量测试，检查覆盖率
6. 循环直到覆盖率达标或所有方法已测试

### Subagent (UT Writer)

文件位置: `/home/twinkle/app/808/Agent_UT_deepseek/prompts/SUBAGENT_UT_PROMPT.md`

作为 Claude Code 内置 Agent 工具的自定义 subagent 定义。包含完整的测试编写规则、命令模板、返回格式。

---

## Project Structure

```
/home/twinkle/app/808/Agent_UT_deepseek/
├── CLAUDE.md                         # Orchestrator 指令 (核心入口)
├── Plan/
│   └── orchestrator-architecture.md  # 本架构设计文档
├── Rule/
│   ├── Java_UT_Testing_Rules.md      # Java UT 编写规范 (已存在)
│   ├── Long_Running_Agent_Rules.md   # 长时间运行 Agent 规范 (已存在)
│   └── subagent-guide.md            # Claude Code Subagent 使用指南 (已存在)
├── prompts/
│   ├── SUBAGENT_UT_PROMPT.md         # Subagent UT 编写提示词
│   └── ORCHESTRATOR_LOOP.md          # Orchestrator 循环提示词模板
├── shared/                           # 状态文件目录
│   ├── class_list.json
│   ├── test_plan.json
│   ├── progress.txt
│   └── coverage_report.json
└── dianping/                         # Java 项目 (已存在)
    ├── pom.xml
    └── src/
```

---

## Orchestrator 启动方式

### 方式 1: 直接启动 (推荐)

```bash
cd /home/twinkle/app/808/Agent_UT_deepseek && claude
```

Claude Code 读取 `CLAUDE.md` 自动进入 Orchestrator 角色：
- 检查 `shared/` 目录状态
- 如果是首次运行 → Phase 1 扫描
- 如果有未测方法 → Phase 2 派发
- 如果覆盖率未达标 → Phase 3 评估 → 循环

### 方式 2: Ralph Loop 自动循环

```bash
# 在 Claude Code 会话中:
/ralph-loop:ralph-loop "执行 UT 生成的下一轮迭代。按照 CLAUDE.md 的 Orchestrator 流程。" --max-iterations 200 --completion-promise "ALL_TESTS_COMPLETE"
```

### 方式 3: Cron 定时触发 (生产环境)

```bash
# 每30分钟执行一轮
*/30 * * * * cd /home/twinkle/app/808/Agent_UT_deepseek && claude --print "执行一轮 UT 生成迭代"
```

---

## Subagent Dispatch Protocol

### Orchestrator 派发 Subagent 的具体步骤

```
Orchestrator:
  1. 读取 class_list.json，找出 test_status=pending 的方法
  2. 按类分组，避免同一类被多个 Subagent 同时修改
  3. 选择 N 个不同类的方法 (N = batch_size, 建议 3-5)
  4. 对每个选中的方法，使用 Agent 工具创建 Subagent:
     - subagent_type: "general-purpose"
     - model: "sonnet" (UT 编写不需要最强模型)
     - description: "UT method: {ClassName}.{methodName}"
     - prompt: 包含完整任务描述和测试规范
  5. 收集每个 Subagent 的返回结果
  6. 更新 class_list.json 和 progress.txt
  7. 检查是否所有方法已测试 → 是则进入 Phase 3
  8. 继续循环
```

### Subagent 返回格式

每个 Subagent 必须以 JSON 格式返回结果：

```json
{
  "status": "pass",
  "class_name": "ShopServiceImpl",
  "method_name": "queryById",
  "test_method": "shouldReturnShopWhenIdExists",
  "test_file": "src/test/java/com/hmdp/service/impl/ShopServiceImplTest.java",
  "error": null,
  "duration_ms": 45
}
```

### 错误处理

| 场景 | 处理方式 |
|------|---------|
| Subagent 失败 (mvn test 不通过) | 标记 test_status=fail，下一轮重试 (最多 3 次) |
| Subagent 超时 (超过 5 分钟) | 终止 Subagent，标记为 fail，降低优先级 |
| 文件冲突 (同一类同时被写) | 确保派发时不同 Subagent 操作不同类 |
| 编译错误 | Subagent 自行修复后重试，3 次不通过则报告失败 |

---

## 与现有 Agent_UT 的对比

| 维度 | 现有 Agent_UT | 新 Agent_UT_deepseek |
|------|--------------|---------------------|
| 架构模式 | Planner→Generator→Evaluator 串行 | Orchestrator + 并行 Subagents |
| 粒度 | 类级别 | **方法级别** (一个 Subagent 一个方法) |
| 并行性 | 单线程 | **多 Subagent 并行** (3-5 个同时) |
| 外部依赖 | Python Harness + Ralph Loop | **零外部依赖** (纯 Claude Code) |
| 测试验证 | Evaluator 集中运行 | **Subagent 自己运行** (即时反馈) |
| 上下文膨胀 | Generator 上下文大 (一次读整个类) | Subagent 上下文小 (一次只读一个方法) |
| 故障隔离 | 一处失败影响整个类 | 一处失败只影响一个方法 |

---

## Implementation Steps

### Step 1: 创建 CLAUDE.md (Orchestrator 主指令)

创建 `/home/twinkle/app/808/Agent_UT_deepseek/CLAUDE.md`，包含：
- 角色定义：我是 UT Generation Orchestrator
- 启动流程：读取 shared/ → 判断 phase → 执行任务
- Phase 1 指令：扫描项目，生成 class_list.json 和 test_plan.json
- Phase 2 指令：派发 Subagent，收集结果，更新状态
- Phase 3 指令：运行全量测试，检查覆盖率，决定是否继续
- 循环规则：覆盖率达标或所有方法已处理时退出

### Step 2: 创建 Subagent Prompt 模板

创建 `prompts/SUBAGENT_UT_PROMPT.md`，包含：
- Subagent 身份和任务描述
- 测试编写规则 (引用 Rule/Java_UT_Testing_Rules.md)
- Maven 命令模板
- 返回格式规范
- Mock 规则

### Step 3: 创建 shared/ 目录结构

创建 `shared/` 目录，包含初始的空状态文件模板。

### Step 4: 初始化并首次运行

```bash
cd /home/twinkle/app/808/Agent_UT_deepseek && claude
# Orchestrator 自动执行 Phase 1 扫描项目
```

### Step 5: 验证循环

- 确认 Subagent 可以成功创建和运行
- 确认状态文件正确更新
- 确认覆盖率逐步提升
- 确认覆盖率达标后自动退出

---

## Verification

### 功能验证

```
□ CLAUDE.md 正确引导 Claude Code 进入 Orchestrator 角色
□ Phase 1: 正确扫描 dianping/src/main/java/ 并生成 class_list.json
□ Phase 2: 成功通过 Agent 工具派发 Subagent
□ Subagent: 正确编写 JUnit 5 测试方法 (AAA 模式, 命名规范)
□ Subagent: 成功运行 mvn test -Dtest= 并返回结果
□ Orchestrator: 正确收集结果并更新 shared/ 文件
□ Phase 3: 正确运行全量 mvn test + jacoco:report
□ 循环: 覆盖率未达标时自动进入下一轮
□ 退出: 覆盖率达标后输出 ALL_TESTS_COMPLETE
□ 故障处理: Subagent 失败时不阻塞整体流程
```

### 运行验证

```bash
# 1. 验证 Orchestrator 启动
cd /home/twinkle/app/808/Agent_UT_deepseek
cat CLAUDE.md  # 确认指令正确

# 2. 验证 Phase 1 扫描
# 在 Claude Code 中运行: "执行 Phase 1 扫描项目"

# 3. 验证 Subagent 独立运行
# Orchestrator 派发一个 Subagent 测试单个方法

# 4. 验证覆盖率流程
cd dianping
/home/twinkle/app/maven/bin/mvn test
cat target/site/jacoco/index.html | grep -o 'Total.*[0-9]*%'
```

### 质量目标

| 指标 | 目标 |
|------|------|
| 行覆盖率 | >= 70% |
| 分支覆盖率 | >= 60% |
| Subagent 成功率 | >= 90% |
| 每轮并行 Subagent 数 | 3-5 |
| 单个 Subagent 执行时间 | < 5 分钟 |

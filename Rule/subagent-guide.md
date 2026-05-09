# Claude Code Subagents 使用指南

> 来源：https://code.claude.com/docs/zh-CN/sub-agents

## 什么是 Subagents

Subagents 是处理特定类型任务的专门 AI 助手。当辅助任务会产生大量搜索结果、日志或文件内容，而您不会再次引用这些内容时，使用 subagent：它在独立上下文中完成工作，仅返回摘要。

**核心价值：**
- 保留主对话上下文
- 强制执行工具限制
- 跨项目重用配置
- 专门化行为
- 控制成本（可使用更快更便宜的模型如 Haiku）

---

## 内置 Subagents

| Agent | Model | 用途 |
| :---- | :---- | :--- |
| **Explore** | Haiku | 快速只读搜索和分析代码库 |
| **Plan** | inherit | 规划期间的代码库研究 |
| **General-purpose** | inherit | 复杂多步骤任务 |

---

## 创建 Subagent（YAML + Markdown 格式）

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep, Bash
model: sonnet
---

You are a code reviewer...
```

### 常用 Frontmatter 字段

| 字段 | 必填 | 说明 |
| :--- | :--- | :--- |
| `name` | Yes | 唯一标识符（小写+连字符） |
| `description` | Yes | Claude 何时委托给此 agent |
| `tools` | No | 允许的工具列表 |
| `disallowedTools` | No | 禁止的工具列表 |
| `model` | No | `sonnet`/`opus`/`haiku`/`inherit` |
| `permissionMode` | No | `default`/`acceptEdits`/`auto`/`dontAsk`/`bypassPermissions` |
| `skills` | No | 预加载的技能列表 |
| `memory` | No | `user`/`project`/`local` — 持久内存 |
| `isolation` | No | `worktree` — 在独立 git worktree 中运行 |
| `background` | No | `true` 始终后台运行 |
| `maxTurns` | No | 最大代理轮数 |

---

## 工具控制

```yaml
# 只允许只读工具
tools: Read, Grep, Glob, Bash

# 继承所有工具但禁止写入
disallowedTools: Write, Edit
```

---

## 调用方式

1. **自然语言**：直接提及 agent 名称
2. **@-mention**：确保特定 agent 运行
3. **会话范围**：`claude --agent <name>`

---

## 内存功能

- `user`: `~/.claude/agent-memory/<name>/` — 跨项目共享
- `project`: `.claude/agent-memory/<name>/` — 可版本控制
- `local`: `.claude/agent-memory-local/<name>/` — 不检入版本控制

---

## 常用模式

- **隔离高容量操作**：测试、日志处理等
- **并行研究**：多个 subagent 同时工作
- **链接**：顺序使用多个 subagent

---

## 分叉（Fork）

启用：`CLAUDE_CODE_FORK_SUBAGENT=1`

分叉继承完整对话历史，而命名 subagent 从新上下文开始。适合需要相同背景的多任务处理。

---

## 示例：代码审查者

```markdown
---
name: code-reviewer
description: 主动审查代码质量、安全性和可维护性
tools: Read, Grep, Glob, Bash
model: inherit
---

你是高级代码审查员。收到调用时：
1. 运行 git diff 查看最近更改
2. 聚焦修改的文件
3. 立即开始审查

审查清单：
- 代码清晰可读
- 函数和变量命名良好
- 无重复代码
- 适当的错误处理
- 无暴露的 secrets 或 API keys
- 已实现输入验证
- 良好的测试覆盖

按优先级组织反馈：
- Critical（必须修复）
- Warnings（应该修复）
- Suggestions（考虑改进）

包含具体的修复示例。
```
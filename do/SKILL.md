---
name: do
description: 显式激活 do 编排技能。输入 $do 后，按 /do 或 /do-csv 协议执行多代理任务编排。
metadata:
  tags: orchestrator, do, multi-agent, csv
---

# do

当用户显式输入 `$do` 或明确要求使用 do skills 时，激活本技能。

## 触发规则

- 输入形如 `/do <task description>` 时：
  1. 读取 `~/.codex/protocols/do-feature.md`
  2. 严格按 5 阶段编排执行
  3. 状态写入当前项目 `.codex/tasks/`
- 输入形如 `/do-csv <csv path>` 时：
  1. 读取 `~/.codex/protocols/do-csv.md`
  2. 解析依赖并按 wave 并行执行
  3. 状态写入当前项目 `.codex/tasks/`
- 输入仅为 `/do-csv`（无路径）时：恢复最近一次未完成 CSV 任务。

## 子代理来源

使用 `~/.codex/agents/` 下的角色配置：

- `architect.toml`
- `developer.toml`
- `explorer.toml`
- `reviewer.toml`

## 行为约束

- 编排器本体不直接改代码，代码改动由 `developer` 子代理完成。
- 保持最小变更，不做无关重构。
- 默认保持兼容性，除非用户明确允许破坏性变更。

## 稳定性契约（强制）

- 对 `/do-csv` 的状态与报告落盘，必须使用 `apply_patch`；禁止使用复杂 shell heredoc/重定向拼接 JSON/Markdown。
- 每次 `/do-csv` 执行后，必须保证 `.codex/tasks/csv-checkpoint.json` 是合法 JSON，且字段完整：`csv_path`、`updated_at`、`status`、`completed_waves`、`completed_task_ids`、`pending_task_ids`、`stop_reason`、`next_resume_command`。
- 执行 `wave` 后立刻写对应 `csv-wave<N>-report.md`，禁止把所有落盘放到最后一步。
- 如果用户要求只跑部分 wave，必须在停止前先写 checkpoint 和 wave 报告，再返回消息。
- 若执行时间过长或遇到阻塞，优先落盘当前进度，再返回可恢复状态，不允许“已执行但未持久化”的结束状态。
- 当本轮请求的必需文件都已落盘后，必须立即返回最终总结，不再做额外扫描。
- 若用户给出精确文件名/格式，必须逐字遵守，不允许改名或改字段。
- `/do-csv` 返回前必须执行收尾守护脚本：`python ~/.codex/skills/do/scripts/csv_artifact_guard.py --task-dir .codex/tasks`；若脚本修复了缺失产物，需在总结中说明。

## 最小交互

- 当用户只输入 `$do` 时，先确认已激活，再要求用户给出任务描述。
- 激活确认文案：
  - `[do] 已激活，请给出 /do 任务描述或 /do-csv 路径。`

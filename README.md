# CodexSkills

可复用的 Codex skills 工作区，重点包含 `do` 编排技能与多代理配置。

## 包含内容

- `do/`：`$do` 显式激活技能、`/do` 与 `/do-csv` 协议、agents 配置、CSV 收尾守护脚本。
- `remotion-best-practices/`：Remotion 领域规则技能。
- `skill-creator/`、`skill-installer/`：技能创建与安装工具。

## 快速安装（推荐）

```bash
git clone https://github.com/wscffaa/CodexSkills.git
cd CodexSkills/do
bash scripts/install_to_codex.sh
```

安装完成后重启 Codex 会话。

## 在 Codex 中调用 `do`

```text
$do
/do <任务描述>
/do-csv <csv路径>
/do-csv
```

- `$do`：显式激活技能。
- `/do`：单任务 5 阶段编排。
- `/do-csv <csv路径>`：按依赖 wave 执行。
- `/do-csv`：从 `.codex/tasks/csv-checkpoint.json` 续跑。

## 稳定性设计（do）

- `/do-csv` 的 checkpoint/report 统一要求 `apply_patch` 落盘。
- 每个 wave 完成后立即落盘 `csv-wave<N>-report.md` 与 checkpoint。
- 返回前执行守护脚本，自动补齐缺失产物：
  `python ~/.codex/skills/do/scripts/csv_artifact_guard.py --task-dir .codex/tasks`
- `status=done` 时要求至少存在：
  `csv-checkpoint.json`、所有已完成 wave 报告、`csv-resume-report.md`、`csv-done.flag`。

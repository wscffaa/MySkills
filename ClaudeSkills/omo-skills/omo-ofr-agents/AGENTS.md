# OMO-OFR Agents 索引

> OFR 多代理套件，**多模型协作**实现论文→代码→实验→SCI 论文的高效产出。

## 多模型后端分配

```
┌────────────────────────────────────────────────────────────────┐
│              实际可用配置 · 9 个专家代理                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Claude (Anthropic) ─ 推理与写作 [付费]                         │
│  ├── Opus 4.5:   ofr-sisyphus, ofr-oracle                     │
│  └── Sonnet 4.5: ofr-librarian, ofr-paper-writer, ofr-codegen │
│                  ofr-explore, ofr-remote-operator              │
│                                                                │
│  Gemini (Google) ─ 多模态理解 [免费额度]                        │
│  └── 2.0-Flash:  ofr-visualization-engineer, ofr-multimodal   │
│                                                                │
│  DeepSeek [可选] ─ 低成本替代                                   │
│  └── Coder-V2:   ofr-codegen, ofr-explore (budget mode)       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## 核心代理

| Agent | 后端 | 模型 | 免费 | 角色 | 可并行 |
|-------|------|------|------|------|--------|
| `ofr-sisyphus` | Claude | Opus 4.5 | ❌ | 总编排/门控 | ❌ |
| `ofr-oracle` | Claude | Opus 4.5 | ❌ | 架构决策/消融矩阵 | ❌ |
| `ofr-librarian` | Claude | Sonnet 4.5 | ❌ | 文献研究/novelty | ✅ |
| `ofr-explore` | Claude | Sonnet 4.5 | ❌ | 代码定位 | ✅ |
| `ofr-codegen` | Claude | Sonnet 4.5 | ❌ | 代码生成 | ❌ |

## 专项代理

| Agent | 后端 | 模型 | 免费 | 角色 | 可并行 |
|-------|------|------|------|------|--------|
| `ofr-visualization-engineer` | Gemini | 2.0-Flash | ✅ | 可视化/Debug | ✅ |
| `ofr-paper-writer` | Claude | Sonnet 4.5 | ❌ | SCI 写作 | ❌ |
| `ofr-multimodal-looker` | Gemini | 2.0-Flash | ✅ | 读图分析 | ✅ |
| `ofr-remote-operator` | Claude | Sonnet 4.5 | ❌ | 远程运维 | ❌ |

## 并行执行组

| 组名 | 可并行代理 | 最大并发 | 场景 |
|------|------------|----------|------|
| `idea_understanding` | librarian + explore + multimodal | 3 | Idea 阶段理解 |
| `exp_monitoring` | visualization + multimodal | 2 | 实验监控 |

## 文件结构

```
.claude/skills/omo-ofr-agents/
├── SKILL.md                    # 主技能定义（路由 + 多模型协作）
├── AGENTS.md                   # 本文件（索引）
└── references/
    ├── models.json             # 多模型后端配置  ← NEW
    ├── ofr-sisyphus.md
    ├── ofr-oracle.md
    ├── ofr-librarian.md
    ├── ofr-explore.md
    ├── ofr-codegen.md
    ├── ofr-visualization-engineer.md
    ├── ofr-paper-writer.md
    ├── ofr-multimodal-looker.md
    └── ofr-remote-operator.md
```

## 与 ofr-pipeline 三阶段的映射

```
ofr-pipeline 阶段    主责代理              辅助代理              后端
──────────────────────────────────────────────────────────────────────
idea
├── source          ofr-sisyphus          ofr-librarian        Claude
├── analyzer        ofr-librarian ║       ofr-oracle          Claude
│                   ofr-explore   ║       ofr-multimodal      OpenCode/Gemini
│                   (可并行 ↑)
└── codegen         ofr-codegen           ofr-explore          Codex

exp
├── train           ofr-remote-operator   ofr-visualization ║  Codex/Gemini
│                                         ofr-multimodal   ║
│                                         (可并行 ↑)
└── test            ofr-remote-operator   ofr-multimodal       Codex/Gemini

paper
├── table           ofr-paper-writer      -                    Claude
└── generate        ofr-paper-writer      ofr-multimodal       Claude/Gemini
```

## 快速调用

### 串行调用
```bash
# 文献分析 (Claude Sonnet)
codeagent-wrapper --agent ofr-librarian - . <<'EOF'
分析 arXiv:2501.xxxxx 论文的创新点
EOF

# 代码定位 (OpenCode Grok)
codeagent-wrapper --agent ofr-explore - . <<'EOF'
找到 BasicOFR 中 SSM 模块的注册位置
EOF

# 架构决策 (Claude Opus)
codeagent-wrapper --agent ofr-oracle - . <<'EOF'
为 WaveMamba 设计集成方案和消融矩阵
EOF
```

### 并行调用
```bash
# 同时启动 3 个不同后端的代理
codeagent-wrapper --agent ofr-librarian - . <<'EOF' &  # Claude
分析论文创新点
EOF

codeagent-wrapper --agent ofr-explore - . <<'EOF' &     # OpenCode
定位 BasicOFR 集成点
EOF

codeagent-wrapper --agent ofr-multimodal-looker - . <<'EOF' &  # Gemini
分析论文架构图
EOF

wait  # 等待全部完成，汇总结果
```

## 配置文件

模型配置位于 `references/models.json`，可自定义后端和模型选择。

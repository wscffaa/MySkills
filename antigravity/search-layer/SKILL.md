---
name: search-layer
description: >
  搜索专用 Skill。用户对话中出现「搜索」「调研」「查一下」「search」「找一下」
  「帮我看看」等关键词时自动激活。提供意图感知的五源并行检索（search_web +
  GrokSearch MCP + Exa + Tavily + Grok-completions），自动分类查询意图、
  调整搜索策略、评分排序、结构化合成。所有搜索需求必须经此 Skill 路由。
---

# Search Layer v3.0-antigravity — 意图感知多源检索协议

五源同级：`search_web` + GrokSearch MCP + Exa + Tavily + Grok-completions。
按意图自动选策略、调权重、做合成。

## 执行流程

```
用户查询
    ↓
[Phase 1] 意图分类 → 确定搜索策略
    ↓
[Phase 2] 查询分解 & 扩展 → 生成子查询（中英双语）
    ↓
[Phase 3] 五源并行检索
    ├─ search_web(query)                              ← 通用网络搜索
    ├─ mcp_grok-websearch_web_search(query)           ← Grok AI 深度搜索
    └─ run_command: python3 search.py --mode deep     ← Exa + Tavily + Grok-completions
    ↓
[Phase 4] 结果合并 & 排序 → 去重 + 意图加权评分
    ↓
[Phase 5] 知识合成 → 结构化输出
```

---

## Phase 1: 意图分类

收到搜索请求后，**先判断意图类型**，再决定搜索策略。不要问用户用哪种模式。

| 意图 | 识别信号 | Mode | Freshness | 权重偏向 |
|------|---------|------|-----------|---------| 
| **Factual** | "什么是 X"、"X 的定义"、"What is X" | answer | — | 权威 0.5 |
| **Status** | "X 最新进展"、"X 现状"、"latest X" | deep | pw/pm | 新鲜度 0.5 |
| **Comparison** | "X vs Y"、"X 和 Y 区别" | deep | py | 关键词 0.4 + 权威 0.4 |
| **Tutorial** | "怎么做 X"、"X 教程"、"how to X" | answer | py | 权威 0.5 |
| **Exploratory** | "深入了解 X"、"X 生态"、"about X" | deep | — | 权威 0.5 |
| **News** | "X 新闻"、"本周 X"、"X this week" | deep | pd/pw | 新鲜度 0.6 |
| **Resource** | "X 官网"、"X GitHub"、"X 文档" | fast | — | 关键词 0.5 |

**判断规则**：
1. 扫描查询中的信号词
2. 多个类型匹配时选最具体的
3. 无法判断时默认 `exploratory`

---

## Phase 2: 查询分解 & 扩展

根据意图类型，将用户查询扩展为一组子查询：

### 通用规则
- **技术同义词自动扩展**：k8s→Kubernetes, JS→JavaScript, Go→Golang
- **中英双语**：中文查询同时生成英文变体

### 按意图扩展

| 意图 | 扩展策略 | 示例 |
|------|---------|------|
| Factual | 加 "definition"、"explained" | "WebTransport" → +  "WebTransport explained overview" |
| Status | 加年份、"latest"、"update" | "Deno 进展" → + "Deno 2.0 latest 2026" |
| Comparison | 拆成 3 个子查询 | "Bun vs Deno" → "Bun vs Deno", "Bun advantages", "Deno advantages" |
| Tutorial | 加 "tutorial"、"guide" | "Rust CLI" → + "Rust CLI tutorial guide step by step" |
| Exploratory | 拆成 2-3 个角度 | "RISC-V" → "overview", "ecosystem", "use cases" |
| News | 加 "news"、日期 | "AI 新闻" → + "AI news this week 2026" |
| Resource | 加资源类型 | "MCP" → + "MCP official documentation GitHub" |

---

## Phase 3: 五源并行检索

**所有源并行调用**，不等一个完成再调另一个。

### 源 1: search_web（通用网络搜索，始终调用）

```
search_web(query="子查询")
```

### 源 2: GrokSearch MCP（AI 深度搜索，始终调用）

```
mcp_grok-websearch_web_search(query="子查询")
```

GrokSearch 会自动浏览网页、汇总答案，返回 session_id + content + sources_count。

### 源 3: search.py（Exa + Tavily + Grok-completions，deep/answer 模式调用）

```bash
python3 /Users/caifeifan/.gemini/antigravity/skills/search-layer/scripts/search.py \
  --queries "子查询1" "子查询2" "子查询3" \
  --mode deep \
  --intent status \
  --freshness pw \
  --num 5
```

**各模式源参与矩阵**：
| 模式 | Exa | Tavily | Grok-completions | 说明 |
|------|-----|--------|------|------|
| fast | ✅ | ❌ | fallback | Exa 优先 |
| deep | ✅ | ✅ | ✅ | 三源并行 |
| answer | ❌ | ✅ | ❌ | 仅 Tavily（含 AI answer） |

**search.py 参数**：
| 参数 | 说明 |
|------|------|
| `--queries` | 多子查询并行 |
| `--mode` | fast / deep / answer |
| `--intent` | 意图类型，影响评分权重 |
| `--freshness` | pd(24h) / pw(周) / pm(月) / py(年) |
| `--domain-boost` | 逗号分隔域名，+0.2 权威分 |
| `--num` | 每源每查询结果数 |

### 源 4: Context7（涉及库/框架时调用）

查询涉及具体第三方库/框架时追加调用：

```
mcp_context7_resolve-library-id(libraryName="库名", query="问题")
→ mcp_context7_query-docs(libraryId="/org/project", query="问题")
```

### 源 5: 秘塔搜索（按需，中文学术场景）

涉及中文学术论文或中文领域概况时追加调用：

```
mcp_metaso_metaso_web_search(q="关键词", scope="paper", includeSummary=true)
```

### 合并规则

将所有源结果合并。按 canonical URL 去重，标记来源。search.py 返回的 `score` 字段优先排序。

---

## Phase 3.5: 引用追踪（Thread Pulling）

当结果中包含 GitHub issue/PR 链接，且意图为 Status 或 Exploratory 时，自动触发。

```bash
# 批量提取引用
python3 /Users/caifeifan/.gemini/antigravity/skills/search-layer/scripts/search.py \
  "query" --mode deep --intent status --extract-refs

# 单 URL 深度抓取
python3 /Users/caifeifan/.gemini/antigravity/skills/search-layer/scripts/fetch_thread.py \
  "https://github.com/owner/repo/issues/123" --format markdown
```

---

## Phase 4: 结果排序

### 评分公式

```
score = w_keyword × keyword_match + w_freshness × freshness_score + w_authority × authority_score
```

权重由意图决定（见 Phase 1 表格）。各分项：
- **keyword_match** (0-1)：查询词在标题+摘要中的覆盖率
- **freshness_score** (0-1)：越新越高（无日期=0.5）
- **authority_score** (0-1)：基于域名权威等级
  - Tier 1 (1.0): github.com, stackoverflow.com, 官方文档站
  - Tier 2 (0.8): HN, dev.to, 知名技术博客
  - Tier 3 (0.6): Medium, 掘金, InfoQ
  - Tier 4 (0.4): 其他

### Domain Boost

```bash
python3 search.py "query" --mode deep --intent tutorial --domain-boost dev.to,freecodecamp.org
```

---

## Phase 5: 知识合成

### 小结果集（≤5 条）
逐条展示，带源标签和评分：
```
1. [Title](url) — snippet... `[search_web, exa]` ⭐0.85
```

### 中结果集（5-15 条）
按主题聚类 + 每组摘要。

### 大结果集（15+ 条）
高层综述 + Top 5 + 深入提示。

### 合成规则
- **先给答案，再列来源**
- **按主题聚合，不按来源聚合**
- **冲突信息显性标注**
- 多源一致 + 新鲜 → 直接陈述
- 单源或较旧 → "根据 [source]，..."
- 冲突 → "存在不同说法：A 认为...，B 认为..."

---

## 降级策略

- search.py 失败 → 继续 search_web + GrokSearch
- GrokSearch MCP 失败 → 继续 search_web + search.py
- search_web 失败 → 继续 GrokSearch + search.py
- **永远不要因为某个源失败而阻塞主流程**

---

## 快速参考

| 场景 | 调用组合 |
|------|---------|
| 快速事实 | `search_web` + `mcp_grok-websearch_web_search` + `search.py --mode answer --intent factual` |
| 深度调研 | `search_web` + `mcp_grok-websearch_web_search` + `search.py --mode deep --intent exploratory` |
| 最新动态 | `search_web` + `mcp_grok-websearch_web_search` + `search.py --mode deep --intent status --freshness pw` |
| 对比分析 | `search_web` × N + `mcp_grok-websearch_web_search` + `search.py --queries "A vs B" "A pros" "B pros" --intent comparison` |
| 找资源 | `search_web` + `search.py --mode fast --intent resource` |
| 中文论文 | `mcp_metaso_metaso_web_search(scope="paper")` + `search_web` |
| 库/框架文档 | `mcp_context7_query-docs` + `search_web` + `mcp_grok-websearch_web_search` |

---

## 配置

API Keys 存储在 skill 目录下 `credentials/search.json`（即 `~/.gemini/antigravity/skills/search-layer/credentials/search.json`）：
```json
{
  "exa": "your-exa-key",
  "tavily": "your-tavily-key",
  "grok": {
    "apiUrl": "https://your-api/v1",
    "apiKey": "your-key",
    "model": "grok-4.1-fast"
  }
}
```
也支持环境变量：`EXA_API_KEY`、`TAVILY_API_KEY`、`GROK_API_KEY`、`GROK_API_URL`。

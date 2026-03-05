# Docx Template Reformatter 参考资料

本文件用于收纳“不适合塞进 SKILL.md 但会显著提升成功率”的细节：OOXML 分节/分栏规律、关系合并、配置建议与验收项。

## 1. OOXML 关键概念（决定双栏是否生效）

### 1.1 分节属性 `w:sectPr` 的存放位置

- Word 的 section properties 可能出现在两处：
  - **段落级**：`w:pPr/w:sectPr`（更常见、也更容易被误删）
  - **body 级**：`w:body/w:sectPr`（通常位于 document.xml 的最后）
- 语义：`w:pPr/w:sectPr` 是“该 section 的结束标记”，其属性作用于“该段落及其之前、直到上一个分节结束标记之后”的内容。

### 1.2 双栏由 `w:sectPr/w:cols` 控制

- 双栏：`<w:cols w:num="2" .../>`
- 单栏：`w:num` 可能缺失（默认单栏），也可能显式为 `1`

### 1.3 典型版式：摘要区单栏、正文从某标题开始双栏

最常见的实现方式是：
- 在“正文起点（如 0 引言）之前的最后一个段落”放一个 `w:pPr/w:sectPr`，它结束 **摘要区 section（单栏）**；
- 在正文区末尾（模板示例正文的末尾通常是空段落）放一个 `w:pPr/w:sectPr`，其中包含 `w:cols w:num="2"`，它结束 **正文区 section（双栏）**；
- 生成输出时，若清空模板示例正文把“承载双栏 sectPr 的段落”删掉，就会导致“从 0 引言开始仍是单栏”。

## 2. 关系（rels）与部件（parts）迁移要点

### 2.1 必须重写的东西

- `word/document.xml` 内的 `r:embed / r:id / r:link`（形如 `rId123`）
- `word/_rels/document.xml.rels` 中对应的 `<Relationship Id="rId123" Target="..."/>`
- `word/media/*`、`word/embeddings/*` 以及可能的自定义部件路径
- `[Content_Types].xml`：新增图片/对象类型时要补 Default 或 Override

### 2.2 稳妥策略

- 为源文档迁移进来的部件统一加前缀（例如 `src_`），避免与模板同名资源冲突。
- 优先复用源文档 `[Content_Types].xml` 的 Override（对于 `.bin/.vsd/...` 等非图片类型尤其重要）。

## 3. 配置建议（当自动锚点识别失败时）

脚本 `scripts/reformat.py` 支持 `--config`（JSON）。当前版本只做“轻量可控”的配置项，避免过度设计。

### 3.1 示例：仅覆盖正文起点匹配

```json
{
  "tpl_body_start_regexes": ["^0引言$", "^引言$"],
  "src_body_start_regexes": ["^0引言$", "^引言$"]
}
```

### 3.2 示例：覆盖样式映射（解决标题/公式编号对齐等问题）

```json
{
  "style_overrides": {
    "h1": "3",
    "h2": "4",
    "equation_number": "af3",
    "fig_caption": "aa",
    "ref_item": "af7"
  }
}
```

说明：
- `h1/h2`：正文标题层级样式（用于修复标题对齐/间距）
- `equation_number`：公式段落样式（常含 `w:jc` 与制表位，决定公式编号对齐）
- `fig_caption`：图题样式
- `ref_item`：参考文献条目样式

### 3.3 示例：覆盖 front matter 文本（跳过源文档抽取的不确定性）

```json
{
  "front_matter_overrides": {
    "doi": "10.xxxx/xxxxx",
    "cn_title": "中文题名",
    "cn_authors": "作者1，作者2",
    "cn_affil": "（单位…）",
    "cn_abs": "中文摘要…",
    "cn_kw": "关键词1；关键词2",
    "class_no": "TMxxx",
    "en_abs": "English abstract ...",
    "en_kw": "keyword1, keyword2"
  }
}
```

## 4. 验收清单（建议逐条对照模板）

- 版面：正文起点（如 `0 引言`）所在 section 的 `cols_num` 与模板一致（常见为 2）。
- 页眉页脚：保持模板原样（投稿版通常不要求补齐出版信息，但不应被破坏）。
- 图片/公式：打开 Word/WPS 无“图片无法显示/对象丢失/关系错误”提示。
- 样式：关键段落（标题、摘要、关键词、参考文献等）使用模板样式体系；必要时按期刊投稿检查表逐项核验。

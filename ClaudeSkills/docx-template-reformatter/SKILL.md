---
name: docx-template-reformatter
description: 将任意论文/报告的 Word（.docx）按目标期刊/会议模板（.docx）重新排版与重建，保留图片/公式/分节/双栏/页眉页脚，并输出可验收的校验报告；当用户提到“套模板”“按期刊模板排版”“从某章节开始双栏”等需求时使用。
---

# Docx Template Reformatter（论文套模板重排）

## Overview

以“模板为母版”重建投稿版 `.docx`：保留模板的页面设置与样式体系，仅迁移源论文内容（文本/图片/公式/表格等）并做必要的样式与分节（如单栏→双栏）复刻；输出 `.docx` + 结构/关系自检报告，便于对照模板逐项验收。

## 适用场景

- 将已有论文 `.docx` 转成另一期刊模板 `.docx` 版式（含双栏、页眉页脚、页码、标题层级、图题表题、参考文献、作者简介）。
- 需要最大程度保留图片、OMML 公式、OLE/Visio 等嵌入对象，避免“转成纯文本再粘贴”导致丢失。
- 需要可复用、可迭代的工程化流程（Inspect → Reformat → Validate → 人工复核）。

## 约束与原则

- 以模板为真相（Template-as-Source-of-Truth）：不在源论文上“修格式”，而是复制模板作为骨架并注入内容。
- 复刻分节而非强改段落：双栏/页眉页脚/页码/页边距由 `w:sectPr` 控制，必须保留/复刻模板的分节结构。
- 迁移内容同时迁移关系：图片/公式对象依赖 `document.xml.rels` 的 `rId` 与部件文件，必须做 `rId` 重映射与 `[Content_Types].xml` 同步。

## Quick Start

执行一次性重排（推荐先跑一遍，再按报告/模板对照微调配置）：

```bash
python3 "scripts/reformat.py" reformat \
  --source "paper.docx" \
  --template "journal_template.docx" \
  --output "paper_reformatted.docx" \
  --report "reformat_report.md"
```

当脚本无法自动定位“正文起点/分栏切换点/参考文献标题”等锚点时，先生成模板画像再补充配置：

```bash
python3 "scripts/reformat.py" inspect-template --template "journal_template.docx" --out "template_profile.json"
python3 "scripts/reformat.py" inspect-doc --docx "paper.docx" --out "source_profile.json"
```

当标题/公式编号/图题等对齐不符合模板时，优先通过 `--config` 提供 `style_overrides`（按模板的 styleId 强制映射），而不是在代码里硬编码对齐参数。

## 工作流（高成功率路径）

### 1) 生成模板画像（Inspect）

执行 `inspect-template`，输出：
- 样式清单（styleId/styleName）
- 分节边界（每个 section 的 `cols`、`type`、所在段落索引）
- 常见锚点候选（如 `0 引言/Introduction`、`参考文献/References`、`作者简介`）

在模板有“标题区单栏、正文区双栏”的场景，重点确认：模板中承载 `cols num="2"` 的 `w:sectPr` 位于哪个段落（通常是某个空段落的 `w:pPr/w:sectPr`，且该段落位于正文区域的末尾）。

### 2) 运行重排（Reformat）

执行 `reformat`：
- 复制模板作为输出骨架
- 清理模板示例正文，仅保留 front matter 与必要的分节结构件
- 从源论文抽取正文起点后的内容并注入
- 合并关系与部件（图片/嵌入对象/媒体等）并重写 `rId`
- 复刻模板中“正文所在 section”的结束分节段落，以保证 `0 引言` 起双栏等版式生效

当需要提升“标题/图题/公式编号/参考文献/作者简介”一致性时，启用基于模板样式的后处理（脚本默认会做保守的样式应用；模板缺少样例时会自动跳过，避免误伤）。

### 3) 产出校验报告（Validate）

查看 `--report` 输出，重点核对：
- `0 引言` 所在 section 的 `cols_num` 是否与模板一致（例如 2）
- `rId` 引用是否全定义、关系目标文件是否存在
- 样式计数是否包含模板关键样式（可作为验收 checklist）

## 常见问题与处理

- 双栏不生效：优先检查是否误删了承载 `w:pPr/w:sectPr/w:cols` 的模板段落；不要只修改 body-level `w:sectPr`，需复刻模板对应 section 的结束分节段落。
- 图片/公式丢失：检查 `document.xml.rels` 是否缺失 `rId`，以及 `word/media|embeddings` 部件与 `[Content_Types].xml` 是否同步。
- 模板样式不生效：避免把源文档的字体字号等“直接格式”带入；优先让模板 style 控制版式。

## 脚本与资源

- 执行脚本：`scripts/reformat.py`
- 参考资料：`references/api_reference.md`（含 OOXML 分节/关系要点、配置建议、验收项）
- 配置示例：`assets/config.example.json`

要求：Python 3.9+；依赖 `lxml`（用于可靠的命名空间 XPath 与 OOXML 编辑）。

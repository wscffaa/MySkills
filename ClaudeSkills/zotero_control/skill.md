---
name: zotero_control
description: Zotero文献库直接控制
---

# Zotero 文献库控制

直接通过 Zotero Web API v3 管理文献库，无需安装 MCP Server。所有操作通过内置 Python 脚本完成，零依赖。

## 使用方式

所有命令通过 `~/.claude/skills/zotero_control/scripts/zotero_api.py` 执行。

密钥配置在 `~/.claude/skills/zotero_control/config.json`：

```json
{
  "ZOTERO_API_KEY": "your_key",
  "ZOTERO_USER_ID": "your_user_id"
}
```

群组库用 `ZOTERO_GROUP_ID` 替代 `ZOTERO_USER_ID`。环境变量可覆盖 config.json 中的值。

脚本路径缩写：`ZT=~/.claude/skills/zotero_control/scripts/zotero_api.py`

## 命令参考

### search — 搜索文献

```bash
python3 $ZT search --query "machine learning" --limit 10
python3 $ZT search --item-type journalArticle --tag "ai" --sort dateAdded --direction desc
python3 $ZT search --collection "COLLECTION_KEY" --limit 25
```

参数：`--query`, `--qmode` (titleCreatorYear|everything), `--item-type`, `--tag`, `--collection`, `--sort` (dateAdded|dateModified|title|creator), `--direction` (asc|desc), `--limit` (1-100), `--start`

### get — 获取单条文献

```bash
python3 $ZT get --key "ITEM_KEY"
python3 $ZT get --doi "10.1234/example"
```

### cite — 生成引用

```bash
python3 $ZT cite --keys "KEY1,KEY2" --style apa
python3 $ZT cite --keys "KEY1" --style chicago-note-bibliography --format html
```

样式：apa, chicago-note-bibliography, chicago-author-date, mla, ieee, nature, science, cell, ama, vancouver, harvard-cite-them-right, bibtex 及 10000+ CSL 样式。

### fulltext — PDF 全文提取

```bash
python3 $ZT fulltext --key "ITEM_KEY"
python3 $ZT fulltext --key "ITEM_KEY" --start-page 1 --end-page 5
```

前提：PDF 须在 Zotero Desktop 中已完成索引。

### create — 创建文献

```bash
python3 $ZT create --json '{"itemType":"journalArticle","title":"My Paper","creators":[{"creatorType":"author","firstName":"Jane","lastName":"Smith"}],"date":"2024","DOI":"10.1234/example","tags":["ai","ml"]}'
```

脚本会自动获取模板并合并数据，tags 支持字符串数组简写。

### update — 更新文献

```bash
python3 $ZT update --key "ITEM_KEY" --version 42 --json '{"title":"Updated Title"}'
```

version 用于冲突检测，先通过 `get` 获取当前 version。

### delete — 批量删除

```bash
python3 $ZT delete --keys "KEY1,KEY2,KEY3"
```

单次上限 50 条。

### collections — 集合管理

```bash
python3 $ZT collections --action list
python3 $ZT collections --action get --key "COL_KEY"
python3 $ZT collections --action create --name "ML Papers"
python3 $ZT collections --action create --name "Deep Learning" --parent "PARENT_KEY"
python3 $ZT collections --action delete --key "COL_KEY"
```

### tags — 标签管理

```bash
python3 $ZT tags --action list
python3 $ZT tags --action add --key "ITEM_KEY" --tags "ai,research,2024"
python3 $ZT tags --action remove --key "ITEM_KEY" --tags "outdated"
```

### keyinfo — 查看密钥信息

```bash
python3 $ZT keyinfo
```

## 典型工作流

### 文献综述

1. `search` 按主题搜索 → 2. `get` 查看详情 → 3. `fulltext` 提取 PDF → 4. `cite` 生成引用列表

### 文献库整理

1. `collections --action create` 建集合 → 2. `search` 找文献 → 3. `tags --action add` 打标签 → 4. `update` 移入集合

### 批量引用

1. `search` 按标签/集合筛选 → 提取所有 item key → 2. `cite --keys "k1,k2,..."` 一次生成全部引用

## 注意事项

- API Key 获取：https://www.zotero.org/settings/keys
- 速率限制：脚本自动处理 429 和 5xx 重试（指数退避）
- 版本冲突：update 需要正确的 version 号，先 get 再改
- fulltext 依赖 Zotero Desktop 索引，未索引的 PDF 会返回错误

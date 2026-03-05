---
name: midscene
description: This skill should be used when generating AI-powered browser automation tests using Midscene with Puppeteer. Triggers when users request automated UI testing, web scraping with AI understanding, or need to create test scripts that interact with web pages using natural language commands. Supports custom AI model configuration (OpenAI-compatible endpoints) and generates TypeScript test code.
---

# Midscene UI 自动化测试生成器

使用 Midscene 生成 AI 驱动的浏览器自动化测试。

## 工作流程

### Step 1: 获取最新文档

**必须首先执行**: 使用 WebFetch 访问 `https://midscenejs.com/zh/llms.txt` 获取文档索引。

文档分类:
- **Web 自动化**: `/zh/integrate-with-puppeteer.md`, `/zh/web-api-reference.md`
- **Android 自动化**: `/zh/android-getting-started.md`, `/zh/android-api-reference.md`
- **iOS 自动化**: `/zh/ios-getting-started.md`, `/zh/ios-api-reference.md`
- **模型配置**: `/zh/model-config.md`, `/zh/model-common-config.md`
- **JavaScript 优化**: `/zh/use-javascript-to-optimize-ai-automation-code.md`
- **YAML 脚本**: `/zh/automate-with-scripts-in-yaml.md`

### Step 2: 根据用户需求获取详细文档

根据用户的测试场景，使用 WebFetch 获取对应的详细文档:

| 用户需求 | 需要获取的文档 |
|---------|--------------|
| Web/浏览器测试 | `https://midscenejs.com/zh/integrate-with-puppeteer.md` + `https://midscenejs.com/zh/web-api-reference.md` |
| Android 测试 | `https://midscenejs.com/zh/android-getting-started.md` + `https://midscenejs.com/zh/android-api-reference.md` |
| iOS 测试 | `https://midscenejs.com/zh/ios-getting-started.md` + `https://midscenejs.com/zh/ios-api-reference.md` |
| 性能优化 | `https://midscenejs.com/zh/use-javascript-to-optimize-ai-automation-code.md` |
| 模型配置 | `https://midscenejs.com/zh/model-config.md` + `https://midscenejs.com/zh/model-common-config.md` |

### Step 3: 生成测试代码

生成的代码自动从环境变量读取模型配置，无需手动填写：

```typescript
// 模型配置从环境变量自动读取，无需在代码中配置
// 确保已设置以下环境变量（参见 README.md）:
// - MIDSCENE_MODEL_BASE_URL
// - MIDSCENE_MODEL_API_KEY
// - MIDSCENE_MODEL_NAME
// - MIDSCENE_MODEL_FAMILY (可选)
```

## 核心 API 参考

从文档获取后使用，主要 API:
- `agent.aiAct(instruction)` - 执行自然语言描述的操作
- `agent.aiQuery<T>(schema)` - 从页面提取结构化数据
- `agent.aiWaitFor(condition)` - 等待条件满足
- `agent.aiAssert(assertion)` - 断言页面状态
- `agent.aiTap(target)` - 点击元素
- `agent.aiLocate(description)` - 定位元素

## 执行测试

```bash
npm install @midscene/web puppeteer tsx --save-dev
npx tsx <test-file>.ts
```

## 参考资源

- 文档索引: https://midscenejs.com/zh/llms.txt
- Puppeteer 集成: https://midscenejs.com/zh/integrate-with-puppeteer.html
- 模型配置: https://midscenejs.com/zh/model-config.html

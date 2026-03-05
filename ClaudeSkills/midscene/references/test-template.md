# Midscene Puppeteer Test Template

Use this template to generate test scripts. Replace placeholders with actual values.

## Basic Template (单模型配置)

```typescript
import puppeteer from 'puppeteer';
import os from 'node:os';
import { PuppeteerAgent } from '@midscene/web/puppeteer';

// ============ AI 模型配置 - 请填写您的配置 ============
// 如果使用 OpenAI，只需设置 API Key
// 如果使用其他模型，请取消注释并填写对应配置

// OpenAI 配置（默认）
process.env.OPENAI_API_KEY = '<YOUR_OPENAI_API_KEY>';

// 自定义模型配置（可选，取消注释使用）
// process.env.MIDSCENE_MODEL_BASE_URL = '<YOUR_API_ENDPOINT>';
// process.env.MIDSCENE_MODEL_API_KEY = '<YOUR_API_KEY>';
// process.env.MIDSCENE_MODEL_NAME = '<MODEL_NAME>';
// process.env.MIDSCENE_MODEL_FAMILY = '<MODEL_FAMILY>'; // gemini | qwen2.5-vl | doubao-vision

// ============ 配置结束 ============

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({
    width: 1280,
    height: 800,
    deviceScaleFactor: os.platform() === 'darwin' ? 2 : 1,
  });

  const agent = new PuppeteerAgent(page);

  try {
    await page.goto('{{TARGET_URL}}');
    await sleep(3000);

    // {{TEST_STEPS}}

    console.log('Test completed successfully!');
  } catch (error) {
    console.error('Test failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
})();
```

## Multi-Model Template (多模型配置)

```typescript
import puppeteer from 'puppeteer';
import os from 'node:os';
import { PuppeteerAgent } from '@midscene/web/puppeteer';

// ============ 多模型配置 - 请填写您的配置 ============
const MODEL_CONFIGS = {
  openai: {
    baseUrl: 'https://api.openai.com/v1',
    apiKey: '<YOUR_OPENAI_API_KEY>',
    modelName: 'gpt-4o',
    modelFamily: undefined as string | undefined,
  },
  gemini: {
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
    apiKey: '<YOUR_GEMINI_API_KEY>',
    modelName: 'gemini-2.0-flash',
    modelFamily: 'gemini',
  },
  qwen: {
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    apiKey: '<YOUR_QWEN_API_KEY>',
    modelName: 'qwen-vl-max',
    modelFamily: 'qwen2.5-vl',
  },
  doubao: {
    baseUrl: '<YOUR_DOUBAO_ENDPOINT>',
    apiKey: '<YOUR_DOUBAO_API_KEY>',
    modelName: '<YOUR_DOUBAO_MODEL>',
    modelFamily: 'doubao-vision',
  },
};

// 选择使用的模型（修改这里切换模型）
const ACTIVE_MODEL: keyof typeof MODEL_CONFIGS = 'openai';

function setupModel() {
  const config = MODEL_CONFIGS[ACTIVE_MODEL];
  if (config.baseUrl) process.env.MIDSCENE_MODEL_BASE_URL = config.baseUrl;
  if (config.apiKey) process.env.MIDSCENE_MODEL_API_KEY = config.apiKey;
  if (config.modelName) process.env.MIDSCENE_MODEL_NAME = config.modelName;
  if (config.modelFamily) process.env.MIDSCENE_MODEL_FAMILY = config.modelFamily;
}

setupModel();
// ============ 配置结束 ============

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({
    width: 1280,
    height: 800,
    deviceScaleFactor: os.platform() === 'darwin' ? 2 : 1,
  });

  const agent = new PuppeteerAgent(page);

  try {
    await page.goto('{{TARGET_URL}}');
    await sleep(3000);

    // {{TEST_STEPS}}

    console.log('Test completed successfully!');
  } catch (error) {
    console.error('Test failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
})();
```

## Common Test Patterns

### Login Test

```typescript
// Navigate to login page
await page.goto('{{LOGIN_URL}}');
await sleep(2000);

// Click login button/link if needed
await agent.aiAct('click the login button or link');
await sleep(1000);

// Fill credentials
await agent.aiAct('type "{{USERNAME}}" in the username or email field');
await agent.aiAct('type "{{PASSWORD}}" in the password field');

// Submit
await agent.aiAct('click the login or submit button');
await sleep(3000);

// Verify login result
const loginResult = await agent.aiQuery<{ success: boolean; message: string }>(
  '{ success: boolean, message: string }, check if login was successful and get any message shown'
);
console.log('Login result:', loginResult);

if (!loginResult.success) {
  throw new Error(`Login failed: ${loginResult.message}`);
}
```

### Browse/List Test

```typescript
// Navigate to list page
await page.goto('{{LIST_URL}}');
await sleep(3000);

// Wait for list to load
await agent.aiWaitFor('the list or grid of items is visible', { timeout: 15000 });

// Extract list data
const items = await agent.aiQuery<Array<{ title: string; description?: string; price?: number }>>(
  '{ title: string, description?: string, price?: number }[], get all items with their details'
);
console.log('Found items:', items);

// Click on first item
await agent.aiAct('click the first item in the list');
await sleep(2000);

// Get item details
const details = await agent.aiQuery<{ title: string; content: string }>(
  '{ title: string, content: string }, get the item title and main content'
);
console.log('Item details:', details);
```

### Search Test

```typescript
// Navigate to page with search
await page.goto('{{SEARCH_URL}}');
await sleep(2000);

// Perform search
await agent.aiAct('type "{{SEARCH_TERM}}" in the search box');
await agent.aiAct('press Enter or click the search button');
await sleep(3000);

// Wait for results
await agent.aiWaitFor('search results are displayed', { timeout: 10000 });

// Get search results
const results = await agent.aiQuery<Array<{ title: string; url?: string }>>(
  '{ title: string, url?: string }[], get all search result titles and links'
);
console.log('Search results:', results);

// Assert results
await agent.aiAssert('there is at least one search result');
```

### Form Submission Test

```typescript
// Navigate to form page
await page.goto('{{FORM_URL}}');
await sleep(2000);

// Fill form fields
await agent.aiAct('type "{{NAME}}" in the name field');
await agent.aiAct('type "{{EMAIL}}" in the email field');
await agent.aiAct('type "{{MESSAGE}}" in the message or description field');

// Select dropdown if needed
await agent.aiAct('select "{{OPTION}}" from the dropdown');

// Check checkbox if needed
await agent.aiAct('check the terms and conditions checkbox');

// Submit form
await agent.aiAct('click the submit button');
await sleep(3000);

// Verify submission
const result = await agent.aiQuery<{ success: boolean; message: string }>(
  '{ success: boolean, message: string }, check if form was submitted successfully'
);
console.log('Form submission result:', result);
```

### Navigation Test

```typescript
// Start at homepage
await page.goto('{{HOME_URL}}');
await sleep(2000);

// Navigate through menu
await agent.aiAct('click on the "{{MENU_ITEM}}" menu item');
await sleep(2000);

// Verify navigation
await agent.aiAssert('the {{PAGE_NAME}} page is displayed');

// Get page content
const pageInfo = await agent.aiQuery<{ title: string; sections: string[] }>(
  '{ title: string, sections: string[] }, get the page title and main section headings'
);
console.log('Page info:', pageInfo);
```

## Placeholder Reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{MODEL_BASE_URL}}` | AI model API endpoint | `http://localhost:8045/v1` |
| `{{MODEL_API_KEY}}` | API key | `sk-xxx` |
| `{{MODEL_NAME}}` | Model name | `gemini-3-flash` |
| `{{MODEL_FAMILY}}` | Model family | `gemini` |
| `{{TARGET_URL}}` | Website URL to test | `https://example.com` |
| `{{TEST_NAME}}` | Name of the test | `Login Flow` |
| `{{TEST_STEPS}}` | Test step code | See patterns above |
| `{{USERNAME}}` | Test username | `test@example.com` |
| `{{PASSWORD}}` | Test password | `password123` |

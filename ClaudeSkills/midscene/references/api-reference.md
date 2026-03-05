# Midscene Puppeteer API Reference

## PuppeteerAgent

The main class for AI-powered browser automation.

### Constructor

```typescript
import { PuppeteerAgent } from '@midscene/web/puppeteer';

const agent = new PuppeteerAgent(page);
```

### Methods

#### aiAct(instruction: string)

Perform actions described in natural language.

```typescript
// Click actions
await agent.aiAct('click the login button');
await agent.aiAct('click on "Submit" button');

// Type actions
await agent.aiAct('type "hello@example.com" in the email input field');
await agent.aiAct('enter "password123" in the password field');

// Combined actions
await agent.aiAct('type "search term" in search box, hit Enter');

// Scroll actions
await agent.aiAct('scroll down to see more content');
```

#### aiQuery<T>(schema: string)

Extract structured data from the page.

```typescript
// Simple query
const title = await agent.aiString('What is the page title?');

// Structured query
const items = await agent.aiQuery<Array<{ name: string; price: number }>>(
  '{ name: string, price: number }[], find all product names and prices'
);

// Boolean query
const isLoggedIn = await agent.aiBoolean('Is the user logged in?');

// Number query
const count = await agent.aiNumber('How many items are in the cart?');
```

#### aiWaitFor(condition: string, options?: { timeout?: number })

Wait for a condition to be true.

```typescript
// Wait for element
await agent.aiWaitFor('the login form is visible');

// Wait with timeout
await agent.aiWaitFor('page has loaded completely', { timeout: 15000 });

// Wait for content
await agent.aiWaitFor('there is at least one product in the list');
```

#### aiAssert(assertion: string)

Assert something about the page. Throws error if assertion fails.

```typescript
await agent.aiAssert('the page shows a success message');
await agent.aiAssert('user is redirected to dashboard');
await agent.aiAssert('there are no error messages visible');
```

#### aiTap(target: string)

Click on an element described in natural language.

```typescript
await agent.aiTap('the first item in the list');
await agent.aiTap('the close button');
await agent.aiTap('the menu icon');
```

#### aiLocate(description: string)

Find the location of an element.

```typescript
const location = await agent.aiLocate('the search button');
console.log(location); // { x: 100, y: 200, width: 50, height: 30 }
```

## Environment Variables

### Required for Custom Models

| Variable | Description |
|----------|-------------|
| `MIDSCENE_MODEL_BASE_URL` | OpenAI-compatible API endpoint |
| `MIDSCENE_MODEL_API_KEY` | API key for authentication |
| `MIDSCENE_MODEL_NAME` | Model name to use |
| `MIDSCENE_MODEL_FAMILY` | Model family (required for VL mode) |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MIDSCENE_MODEL_MAX_TOKENS` | Max tokens for response | Model default |
| `MIDSCENE_LANGSMITH_DEBUG` | Enable LangSmith debugging | false |
| `MIDSCENE_LANGFUSE_DEBUG` | Enable Langfuse debugging | false |

## Model Families

| Family | Models | Notes |
|--------|--------|-------|
| `gemini` | gemini-pro-vision, gemini-3-flash | Google models |
| `qwen2.5-vl` | qwen2.5-vl-* | Alibaba Qwen 2.5 |
| `qwen3-vl` | qwen3-vl-* | Alibaba Qwen 3 |
| `doubao-vision` | doubao-vision-* | ByteDance Doubao |
| `vlm-ui-tars` | ui-tars-* | UI-TARS models |

## Error Handling

Common errors and solutions:

### vlMode cannot be undefined

**Error**: `vlMode cannot be undefined when includeBbox is true`

**Solution**: Set `MIDSCENE_MODEL_FAMILY` environment variable.

```typescript
process.env.MIDSCENE_MODEL_FAMILY = 'gemini';
```

### Timeout errors

**Error**: `waitFor timeout: ...`

**Solution**: Increase timeout or check if the condition is achievable.

```typescript
await agent.aiWaitFor('condition', { timeout: 30000 });
```

### Element not found

**Error**: `Cannot find element matching description`

**Solution**: Use more specific descriptions or wait for element to appear first.

```typescript
await agent.aiWaitFor('the button is visible');
await agent.aiTap('the button');
```

## Best Practices

1. **Use clear, specific instructions**
   - Good: `click the blue "Submit" button at the bottom of the form`
   - Bad: `click submit`

2. **Add appropriate waits**
   ```typescript
   await page.goto(url);
   await sleep(3000); // Wait for initial load
   await agent.aiWaitFor('page content is loaded');
   ```

3. **Handle dynamic content**
   ```typescript
   await agent.aiWaitFor('the list has at least one item', { timeout: 10000 });
   const items = await agent.aiQuery('...');
   ```

4. **Use structured queries for data extraction**
   ```typescript
   // Define clear schema
   const data = await agent.aiQuery<{
     title: string;
     price: number;
     inStock: boolean;
   }>('{ title: string, price: number, inStock: boolean }, get product details');
   ```

5. **Always close browser in finally block**
   ```typescript
   try {
     // test code
   } finally {
     await browser.close();
   }
   ```

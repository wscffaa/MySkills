# Midscene Skill

使用 Midscene 生成 AI 驱动的浏览器自动化测试。

## 前置要求

在使用此 skill 之前，必须配置以下环境变量：

### 必需环境变量

```bash
# API 端点地址
export MIDSCENE_MODEL_BASE_URL="https://api.openai.com/v1"

# API 密钥
export MIDSCENE_MODEL_API_KEY="your-api-key"

# 模型名称
export MIDSCENE_MODEL_NAME="gpt-4o"
```

### 可选环境变量

```bash
# 模型家族（非 OpenAI 模型需要设置）
export MIDSCENE_MODEL_FAMILY="gemini"  # gemini | qwen2.5-vl | doubao-vision
```

## 常用模型配置示例

### OpenAI

```bash
export MIDSCENE_MODEL_BASE_URL="https://api.openai.com/v1"
export MIDSCENE_MODEL_API_KEY="sk-xxx"
export MIDSCENE_MODEL_NAME="gpt-4o"
```

### Gemini

```bash
export MIDSCENE_MODEL_BASE_URL="https://generativelanguage.googleapis.com/v1beta"
export MIDSCENE_MODEL_API_KEY="your-gemini-key"
export MIDSCENE_MODEL_NAME="gemini-2.0-flash"
export MIDSCENE_MODEL_FAMILY="gemini"
```

### 通义千问 (Qwen)

```bash
export MIDSCENE_MODEL_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export MIDSCENE_MODEL_API_KEY="your-qwen-key"
export MIDSCENE_MODEL_NAME="qwen-vl-max"
export MIDSCENE_MODEL_FAMILY="qwen2.5-vl"
```

### 豆包 (Doubao)

```bash
export MIDSCENE_MODEL_BASE_URL="your-doubao-endpoint"
export MIDSCENE_MODEL_API_KEY="your-doubao-key"
export MIDSCENE_MODEL_NAME="your-doubao-model"
export MIDSCENE_MODEL_FAMILY="doubao-vision"
```

## 持久化配置

建议将环境变量添加到 shell 配置文件中：

```bash
# ~/.zshrc 或 ~/.bashrc
export MIDSCENE_MODEL_BASE_URL="..."
export MIDSCENE_MODEL_API_KEY="..."
export MIDSCENE_MODEL_NAME="..."
export MIDSCENE_MODEL_FAMILY="..."  # 如需要
```

配置后执行 `source ~/.zshrc` 使其生效。

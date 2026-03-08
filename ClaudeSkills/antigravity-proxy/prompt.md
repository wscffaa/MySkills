你是一个专门配置 Antigravity 代理的助手。你的任务是通过 graftcp + mihomo 方案解决 Antigravity AI 聊天连接失败的问题。

**使用场景**：用户在 Mac 本地使用 Antigravity，远程连接到 Docker 容器服务器进行开发，需要通过代理访问 AI 大模型服务。

## 任务流程

### 1. 环境检查
- 检查 mihomo 是否运行（端口 7890/7891）
- 检查 graftcp 是否已安装
- 查找 Antigravity 的 language_server_linux_x64 位置
- 检查是否已配置 cron 自动更新任务

### 2. 安装 graftcp（如果未安装）
```bash
# 下载 graftcp
cd ~ && wget -q https://github.com/hmgle/graftcp/archive/refs/tags/v0.7.1.tar.gz
tar -xzf v0.7.1.tar.gz

# 安装 Go（如果需要）
if ! command -v go &> /dev/null; then
  wget -q https://go.dev/dl/go1.24.7.linux-amd64.tar.gz
  tar -xzf go1.24.7.linux-amd64.tar.gz -C ~
  export PATH=$HOME/go/bin:$PATH
fi

# 编译 graftcp
export GOPROXY=https://goproxy.cn,direct
cd ~/graftcp-0.7.1 && make
```

### 3. 配置 Antigravity 劫持脚本
找到 Antigravity 的二进制文件路径：
```bash
find ~/.antigravity-server -name "language_server_linux_x64" 2>/dev/null | head -1
```

备份并替换为劫持脚本：
```bash
# 备份原文件
cp language_server_linux_x64 language_server_linux_x64.bak

# 创建劫持脚本
cat > language_server_linux_x64 << 'SCRIPT'
#!/usr/bin/env bash
GRAFTCP_DIR="$HOME/graftcp-0.7.1"
PROXY_SOCKS="127.0.0.1:7891"

# 自动启动 graftcp-local
if ! pgrep -f "graftcp-local" > /dev/null; then
  nohup "$GRAFTCP_DIR/local/graftcp-local" -socks5 "$PROXY_SOCKS" -listen 127.0.0.1:2233 -select_proxy_mode only_socks5 > /dev/null 2>&1 &
  sleep 0.5
fi

# Go 优化
export GODEBUG=netdns=cgo,http2client=0

# 执行原程序
exec "$GRAFTCP_DIR/graftcp" -a 127.0.0.1 -p 2233 "$0.bak" "$@"
SCRIPT

chmod +x language_server_linux_x64
```

### 4. 配置自动更新（重要！）
安装 cron 任务，每 5 分钟自动检测 Antigravity 版本更新并应用代理配置：
```bash
~/.codex/skills/antigravity-proxy/install-cron.sh
```

这样当 Antigravity 更新到新版本时，会自动：
- 检测新版本的 language_server_linux_x64
- 备份原文件并创建劫持脚本
- 重启进程使配置生效

### 5. 重启 Antigravity 进程
```bash
pkill -f language_server_linux_x64
```

### 6. 验证配置
```bash
# 检查代理连接
curl -I --socks5-hostname 127.0.0.1:7891 https://daily-cloudcode-pa.googleapis.com

# 检查端口监听
ss -lntp | grep -E '7891|2233'

# 检查进程
ps aux | grep -E 'graftcp-local|language_server'
```

## 重要提示
- mihomo 必须已经运行（通过 supervisor 自动启动）
- **自动更新**：cron 任务每 5 分钟检测 Antigravity 版本更新并自动应用代理配置
- 脚本会自动启动 graftcp-local，无需手动管理
- 容器重启后 mihomo 和 graftcp-local 都会自动恢复
- 日志文件：`/tmp/antigravity-proxy.log`

## 输出格式
完成后输出配置状态表格，包括：
- mihomo 状态
- graftcp 状态
- 劫持脚本状态
- cron 自动更新任务状态
- 代理连接测试结果
- 当前 Antigravity 版本路径

#!/usr/bin/env bash
# Antigravity 代理自动更新脚本

GRAFTCP_DIR="$HOME/graftcp-0.7.1"
ANTIGRAVITY_BASE="$HOME/.antigravity-server/bin"

# 查找最新版本的 language_server_linux_x64
LATEST_SERVER=$(find "$ANTIGRAVITY_BASE" -name "language_server_linux_x64" -type f 2>/dev/null | sort -V | tail -1)

if [ -z "$LATEST_SERVER" ]; then
  echo "未找到 Antigravity language_server"
  exit 1
fi

SERVER_DIR=$(dirname "$LATEST_SERVER")

# 检查是否已经是劫持脚本
if head -1 "$LATEST_SERVER" 2>/dev/null | grep -q "#!/usr/bin/env bash"; then
  echo "✓ 已配置代理劫持: $LATEST_SERVER"
  exit 0
fi

# 备份并创建劫持脚本
echo "→ 发现新版本，正在配置代理..."
cp "$LATEST_SERVER" "$LATEST_SERVER.bak"

cat > "$LATEST_SERVER" << 'SCRIPT'
#!/usr/bin/env bash
GRAFTCP_DIR="$HOME/graftcp-0.7.1"
PROXY_SOCKS="127.0.0.1:7891"

if ! pgrep -f "graftcp-local" > /dev/null; then
  nohup "$GRAFTCP_DIR/local/graftcp-local" -socks5 "$PROXY_SOCKS" -listen 127.0.0.1:2233 -select_proxy_mode only_socks5 > /dev/null 2>&1 &
  sleep 0.5
fi

export GODEBUG=netdns=cgo,http2client=0
exec "$GRAFTCP_DIR/graftcp" -a 127.0.0.1 -p 2233 "$0.bak" "$@"
SCRIPT

chmod +x "$LATEST_SERVER"
echo "✓ 代理配置完成: $LATEST_SERVER"

# 重启进程
pkill -f language_server_linux_x64 2>/dev/null
echo "✓ 已重启 Antigravity 进程"

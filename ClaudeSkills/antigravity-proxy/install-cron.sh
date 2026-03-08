#!/usr/bin/env bash
# 安装 cron 任务，每 5 分钟检查一次

SCRIPT_PATH="$HOME/.codex/skills/antigravity-proxy/auto-update.sh"

# 检查 crontab 是否已存在
if crontab -l 2>/dev/null | grep -q "antigravity-proxy/auto-update.sh"; then
  echo "✓ Cron 任务已存在"
  exit 0
fi

# 添加 cron 任务
(crontab -l 2>/dev/null; echo "*/5 * * * * $SCRIPT_PATH >> /tmp/antigravity-proxy.log 2>&1") | crontab -
echo "✓ 已添加 cron 任务（每 5 分钟检查一次）"
